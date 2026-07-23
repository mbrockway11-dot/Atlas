"""Explain the extreme near-neighbours, under both metrics.

"Zero exact collisions" says little. What matters before any
nearest-neighbour output reaches a user is *why* two unrelated names sit at
the top of the distribution, and whether the same pairs stay extreme when the
geometry changes.

Each extreme pair is classified by cause:

    surface_morphology      length and token structure explain it
    letter_overlap          they share most of their letters
    distributed_feature     no single cause; agreement spread across features
    metric_specific         extreme under one geometry but not the other
    unexplained             none of the above

Rank agreement between the two metrics is reported alongside, because a
geometry can improve resolution while reordering the population wholesale --
which must be understood before adopting it, not after.

    python scripts/explain_extreme_neighbors.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np

from atlas.validation.artifacts import build_provenance, write_json
from atlas.validation.datasets import load_corpus_matrix, name_strata
from atlas.validation.matching import build_matched_index, stratum_keys
from atlas.validation.metrics import METRICS_BY_NAME, upper_triangle
from atlas.validation.models import load_config
from atlas.validation.neighbors import decompose_pair
from atlas.validation.residuals import spearman_correlation
from atlas.validation.statistics import percentile_of, summarize
from atlas.validation.variants import character_overlap, levenshtein


CANONICAL_METRIC = "cosine"
RESEARCH_METRIC = "centered_cosine"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Explain extreme near-neighbours under both metrics."
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
        default=Path("output")
        / "validation"
        / "identity_neighbor_explanation_v1",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Extreme pairs to explain (default: 50).",
    )
    return parser


def _classify(
    *,
    matched_percentile: float,
    letter_overlap: float,
    length_difference: int,
    extreme_in_other_metric: bool,
) -> str:
    """Return the most likely cause of an extreme pair."""
    if not extreme_in_other_metric:
        return "metric_specific"

    if matched_percentile < 95.0:
        return "surface_morphology"

    if letter_overlap >= 0.75:
        return "letter_overlap"

    if length_difference <= 2:
        return "distributed_feature"

    return "unexplained"


def main() -> int:
    """Run the neighbour explanation."""
    args = build_parser().parse_args()
    config = load_config(args.config)
    started = perf_counter()

    corpus = load_corpus_matrix(normalization_mode=config.normalization_mode)
    strata = name_strata(corpus.profile_names)
    lengths = strata["character_length"]
    tokens = strata["token_count"]

    rows, columns = np.triu_indices(corpus.profile_count, k=1)
    pair_indices = np.column_stack((rows, columns))

    scores: dict[str, np.ndarray] = {}
    summaries: dict[str, object] = {}

    for metric_name in (CANONICAL_METRIC, RESEARCH_METRIC):
        metric = METRICS_BY_NAME[metric_name]
        values = upper_triangle(metric.pairwise(corpus.matrix))
        scores[metric_name] = values
        summaries[metric_name] = summarize(values, bins=200)

    labels = stratum_keys(
        token_counts=tokens, char_lengths=lengths, pair_indices=pair_indices
    )

    matched_indexes = {
        name: build_matched_index(scores=values, labels=labels)
        for name, values in scores.items()
    }

    # ---- rank agreement ---------------------------------------------------
    rng = np.random.default_rng(config.random_seed)
    sample = rng.choice(
        scores[CANONICAL_METRIC].size,
        size=min(300_000, scores[CANONICAL_METRIC].size),
        replace=False,
    )

    def top_set(values: np.ndarray, count: int) -> set[int]:
        order = np.argpartition(values, -count)[-count:]
        return set(int(i) for i in order)

    total = scores[CANONICAL_METRIC].size
    overlaps = {}

    for label, count in (
        ("top_10", 10),
        ("top_50", 50),
        ("top_1pct", max(1, total // 100)),
    ):
        canonical_top = top_set(scores[CANONICAL_METRIC], count)
        research_top = top_set(scores[RESEARCH_METRIC], count)
        overlaps[label] = {
            "size": count,
            "shared": len(canonical_top & research_top),
            "fraction": len(canonical_top & research_top) / count,
        }

    rank_agreement = {
        "spearman_sampled": spearman_correlation(
            scores[CANONICAL_METRIC][sample], scores[RESEARCH_METRIC][sample]
        ),
        "pearson": float(
            np.corrcoef(scores[CANONICAL_METRIC], scores[RESEARCH_METRIC])[
                0, 1
            ]
        ),
        "overlaps": overlaps,
        "sample_size": int(sample.size),
    }

    # ---- explain the extremes --------------------------------------------
    canonical_top = np.argsort(scores[CANONICAL_METRIC])[-args.limit :][::-1]
    research_top_set = set(
        int(i)
        for i in np.argpartition(
            scores[RESEARCH_METRIC], -args.limit
        )[-args.limit :]
    )

    records: list[dict] = []
    causes: dict[str, int] = {}

    for row in canonical_top:
        row = int(row)
        left = int(pair_indices[row, 0])
        right = int(pair_indices[row, 1])

        name_a = corpus.profile_names[left]
        name_b = corpus.profile_names[right]

        overlap = character_overlap(name_a, name_b)
        cipher_scores, planet_scores = decompose_pair(corpus, left, right)

        length_difference = int(abs(int(lengths[left]) - int(lengths[right])))
        matched = matched_indexes[CANONICAL_METRIC].matched_percentile(
            float(scores[CANONICAL_METRIC][row]), str(labels[row])
        )

        cause = _classify(
            matched_percentile=matched,
            letter_overlap=overlap["multiset_overlap"],
            length_difference=length_difference,
            extreme_in_other_metric=row in research_top_set,
        )
        causes[cause] = causes.get(cause, 0) + 1

        records.append(
            {
                "name_a": name_a,
                "name_b": name_b,
                "profile_a": corpus.profile_keys[left],
                "profile_b": corpus.profile_keys[right],
                "cosine": float(scores[CANONICAL_METRIC][row]),
                "cosine_percentile": float(
                    percentile_of(
                        summaries[CANONICAL_METRIC],
                        float(scores[CANONICAL_METRIC][row]),
                    )
                ),
                "cosine_matched_percentile": float(matched),
                "centered_cosine": float(scores[RESEARCH_METRIC][row]),
                "centered_cosine_percentile": float(
                    percentile_of(
                        summaries[RESEARCH_METRIC],
                        float(scores[RESEARCH_METRIC][row]),
                    )
                ),
                "centered_cosine_matched_percentile": float(
                    matched_indexes[RESEARCH_METRIC].matched_percentile(
                        float(scores[RESEARCH_METRIC][row]), str(labels[row])
                    )
                ),
                "extreme_under_both_metrics": row in research_top_set,
                "length_difference": length_difference,
                "token_difference": int(
                    abs(int(tokens[left]) - int(tokens[right]))
                ),
                "letter_jaccard": overlap["jaccard"],
                "letter_multiset_overlap": overlap["multiset_overlap"],
                "edit_distance": levenshtein(name_a.lower(), name_b.lower()),
                "dominant_cipher": max(cipher_scores, key=cipher_scores.get),
                "dominant_planet": max(planet_scores, key=planet_scores.get),
                "cipher_scores": cipher_scores,
                "planet_scores": planet_scores,
                "cause": cause,
            }
        )

    survived = sum(
        1 for record in records if record["extreme_under_both_metrics"]
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        {
            "records": records,
            "cause_counts": dict(sorted(causes.items())),
            "extreme_under_both_metrics": survived,
            "verdict": (
                "feature_encoding_degeneracy"
                if survived >= 0.8 * len(records)
                else "cosine_geometry_artifact"
                if survived <= 0.2 * len(records)
                else "mixed"
            ),
        },
        args.output_dir / "neighbor_explanation.json",
    )
    write_json(rank_agreement, args.output_dir / "neighbor_rank_agreement.json")
    write_json(
        build_provenance(
            config,
            profile_count=corpus.profile_count,
            pair_count=int(total),
            block_size=int(config.options.get("block_size", 256)),
        ).to_dict(),
        args.output_dir / "provenance.json",
    )

    print(
        json.dumps(
            {
                "success": True,
                "examined": len(records),
                "cause_counts": dict(sorted(causes.items())),
                "extreme_under_both_metrics": survived,
                "rank_agreement": {
                    "spearman": round(rank_agreement["spearman_sampled"], 4),
                    "pearson": round(rank_agreement["pearson"], 4),
                    "top_10_overlap": overlaps["top_10"]["fraction"],
                    "top_50_overlap": overlaps["top_50"]["fraction"],
                    "top_1pct_overlap": round(
                        overlaps["top_1pct"]["fraction"], 4
                    ),
                },
                "examples": [
                    {
                        "a": record["name_a"],
                        "b": record["name_b"],
                        "cosine": round(record["cosine"], 5),
                        "letter_overlap": round(
                            record["letter_multiset_overlap"], 3
                        ),
                        "len_diff": record["length_difference"],
                        "cause": record["cause"],
                    }
                    for record in records[:10]
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
