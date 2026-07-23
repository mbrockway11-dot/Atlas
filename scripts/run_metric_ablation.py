"""Compare candidate similarity geometries on the full corpus.

Raw cosine compresses: unrelated pairs average 0.959 with a standard
deviation of 0.014, and a random name of matched length scores 0.967. This
asks whether another geometry discriminates better -- and, critically,
whether it does so *without* destroying the invariances the encoding is
supposed to have.

A metric that separates well but no longer treats "Nikola Tesla" and
"nikola  tesla" as the same name has not improved anything. Both properties
are therefore measured together, and no metric is recommended on
discrimination alone.

    python scripts/run_metric_ablation.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np

from atlas.validation.artifacts import build_provenance, write_json
from atlas.validation.datasets import (
    build_feature_layout,
    load_corpus_matrix,
    name_strata,
    vector_for_name,
)
from atlas.validation.metrics import (
    METRICS,
    pair_scores,
    resolution,
    separation,
    spread_ratio,
)
from atlas.validation.models import load_config
from atlas.validation.perturbations import (
    INVARIANCE_TRANSFORMATIONS,
    Expectation,
    length_matched_random,
    shuffle_characters,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Ablate similarity geometries over the corpus."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(
            "configs/validation/identity_random_pair_baseline_v1.yaml"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output") / "validation" / "identity_metric_ablation_v1",
    )
    parser.add_argument(
        "--invariance-names",
        type=int,
        default=80,
        help="Names used for the invariance check (default: 80).",
    )
    return parser


def _pairwise_for_rows(rows: np.ndarray, metric, corpus_matrix: np.ndarray):
    """Score aligned row pairs under a metric, using corpus-level centering.

    Centering and scaling are estimated from the corpus, not from the small
    probe set: a metric must be applied the same way everywhere or its
    numbers are not comparable with the baseline.
    """
    stacked = np.vstack([corpus_matrix, rows])
    full = metric.pairwise(stacked)

    offset = corpus_matrix.shape[0]
    count = rows.shape[0] // 2

    return np.array(
        [full[offset + 2 * i, offset + 2 * i + 1] for i in range(count)]
    )


def main() -> int:
    """Run the metric ablation."""
    args = build_parser().parse_args()
    config = load_config(args.config)
    started = perf_counter()

    corpus = load_corpus_matrix(normalization_mode=config.normalization_mode)
    layout = build_feature_layout()
    strata = name_strata(corpus.profile_names)

    rng = np.random.default_rng(config.random_seed)

    # Probe set for invariance and degeneracy checks.
    probe_count = min(args.invariance_names, corpus.profile_count)
    probe_rows = rng.choice(
        corpus.profile_count, size=probe_count, replace=False
    )
    probe_names = [corpus.profile_names[int(i)] for i in probe_rows]

    # Build the paired probe matrices once; reused by every metric.
    invariant_pairs: list[np.ndarray] = []
    shuffle_pairs: list[np.ndarray] = []
    random_pairs: list[np.ndarray] = []

    invariant_transform = next(
        t
        for t in INVARIANCE_TRANSFORMATIONS
        if t.expectation is Expectation.INVARIANT
    )

    for name in probe_names:
        original = vector_for_name(name, layout=layout)

        if original is None:
            continue

        variants = {
            "invariant": invariant_transform.apply(name),
            "shuffle": shuffle_characters(
                name, rng=np.random.default_rng(abs(hash(name)) % (2**32))
            ),
            "random": length_matched_random(
                name, rng=np.random.default_rng(abs(hash(name)) % (2**32))
            ),
        }

        for key, target in (
            ("invariant", invariant_pairs),
            ("shuffle", shuffle_pairs),
            ("random", random_pairs),
        ):
            vector = vector_for_name(variants[key], layout=layout)

            if vector is not None:
                target.append(np.vstack([original, vector]))

    results: list[dict] = []

    # Structural confounder, computed once and reused per metric.
    rows, columns = np.triu_indices(corpus.profile_count, k=1)
    lengths = strata["character_length"].astype(np.float64)
    tokens = strata["token_count"].astype(np.float64)
    length_difference = np.abs(lengths[rows] - lengths[columns])
    token_difference = np.abs(tokens[rows] - tokens[columns])

    for metric in METRICS:
        scores = pair_scores(corpus.matrix, metric)

        invariance = (
            _pairwise_for_rows(
                np.vstack(invariant_pairs), metric, corpus.matrix
            )
            if invariant_pairs
            else np.array([])
        )
        shuffles = (
            _pairwise_for_rows(
                np.vstack(shuffle_pairs), metric, corpus.matrix
            )
            if shuffle_pairs
            else np.array([])
        )
        randoms = (
            _pairwise_for_rows(np.vstack(random_pairs), metric, corpus.matrix)
            if random_pairs
            else np.array([])
        )

        # Does a genuine invariant stay at the ceiling under this metric?
        ceiling = float(scores.max())
        invariance_preserved = (
            bool(np.all(invariance >= ceiling - 1e-6))
            if invariance.size
            else False
        )

        # The degeneracy test: is a scrambled or random name still closer to
        # the original than an average unrelated pair?
        against_random = (
            separation(shuffles, scores) if shuffles.size else {}
        )

        results.append(
            {
                "metric": metric.name,
                "description": metric.description,
                "pairs": int(scores.size),
                "mean": float(scores.mean()),
                "median": float(np.median(scores)),
                "stddev": float(scores.std()),
                "minimum": float(scores.min()),
                "maximum": float(scores.max()),
                "range": float(scores.max() - scores.min()),
                "spread_ratio": spread_ratio(scores),
                # The measure that matters: how far a known-identical
                # transformation sits above a known-unrelated one, in
                # population standard deviations.
                "resolution_sd": (
                    resolution(
                        invariant_score=float(invariance.mean()),
                        control_score=float(randoms.mean()),
                        population_stddev=float(scores.std()),
                    )
                    if invariance.size and randoms.size
                    else None
                ),
                "confounder_pearson_length": float(
                    np.corrcoef(length_difference, scores)[0, 1]
                ),
                "confounder_pearson_tokens": float(
                    np.corrcoef(token_difference, scores)[0, 1]
                ),
                "invariance": {
                    "transformation": invariant_transform.name,
                    "samples": int(invariance.size),
                    "min_score": (
                        float(invariance.min()) if invariance.size else None
                    ),
                    "preserved": invariance_preserved,
                },
                "degeneracy": {
                    "shuffled_name_mean": (
                        float(shuffles.mean()) if shuffles.size else None
                    ),
                    "random_name_mean": (
                        float(randoms.mean()) if randoms.size else None
                    ),
                    "unrelated_pair_mean": float(scores.mean()),
                    # The headline degeneracy: a scrambled or unrelated name
                    # scoring above the corpus mean means gross morphology,
                    # not identity, is driving the number.
                    "shuffle_above_unrelated_mean": (
                        bool(shuffles.mean() > scores.mean())
                        if shuffles.size
                        else None
                    ),
                    "random_above_unrelated_mean": (
                        bool(randoms.mean() > scores.mean())
                        if randoms.size
                        else None
                    ),
                    "shuffle_vs_unrelated": against_random,
                },
            }
        )

    # A metric is only a candidate if it keeps invariance AND reduces the
    # degeneracy. Discrimination alone is not an improvement.
    # A candidate must keep the invariances. Ranking is then by resolution:
    # how far a known-identical pair sits above a known-unrelated one.
    candidates = [row for row in results if row["invariance"]["preserved"]]

    candidates.sort(key=lambda row: row.get("resolution_sd") or 0.0, reverse=True)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        {
            "metrics": results,
            "recommended": candidates[0]["metric"] if candidates else None,
            "candidate_metrics": [row["metric"] for row in candidates],
            "note": (
                "The canonical Atlas score remains plain cosine. Anything "
                "here is a research lens reported alongside it, never a "
                "replacement."
            ),
        },
        args.output_dir / "metric-ablation.json",
    )
    write_json(
        build_provenance(
            config,
            profile_count=corpus.profile_count,
            pair_count=int(corpus.pair_count),
            block_size=int(config.options.get("block_size", 256)),
        ).to_dict(),
        args.output_dir / "provenance.json",
    )

    print(
        json.dumps(
            {
                "success": True,
                "recommended": candidates[0]["metric"] if candidates else None,
                "metrics": [
                    {
                        "metric": row["metric"],
                        "mean": round(row["mean"], 4),
                        "stddev": round(row["stddev"], 4),
                        "range": round(row["range"], 4),
                        "spread_ratio": round(row["spread_ratio"], 4),
                        "resolution_sd": (
                            round(row["resolution_sd"], 2)
                            if row["resolution_sd"] is not None
                            else None
                        ),
                        "length_confounder_r": round(
                            row["confounder_pearson_length"], 4
                        ),
                        "invariance_preserved": row["invariance"]["preserved"],
                        "random_name_above_mean": row["degeneracy"][
                            "random_above_unrelated_mean"
                        ],
                        "shuffle_above_mean": row["degeneracy"][
                            "shuffle_above_unrelated_mean"
                        ],
                    }
                    for row in results
                ],
                "output_dir": str(args.output_dir),
                "elapsed_seconds": round(perf_counter() - started, 2),
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
