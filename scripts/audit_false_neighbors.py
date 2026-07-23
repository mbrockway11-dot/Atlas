"""Build matched percentiles, the residual model, and the false-neighbour audit.

Answers the question the baseline raised: after controlling for name length
and token structure, does the identity-vector model retain discriminative
signal?

Produces, alongside the audit:

* ``matched-percentile-index.json`` -- per-stratum score distributions, so
  any later pair can be scored against like-shaped names rather than the
  corpus at large
* ``residual-model.json`` -- expected similarity given name structure
* ``confounders.json`` -- Pearson, Spearman, partial correlations, and the
  nonlinear response by exact length difference

    python scripts/audit_false_neighbors.py
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
from atlas.validation.matching import (
    build_matched_index,
    save_matched_index,
    stratum_keys,
)
from atlas.validation.models import load_config
from atlas.validation.neighbors import (
    build_neighbor_records,
    extreme_pairs,
    summarize_false_neighbors,
)
from atlas.validation.residuals import (
    build_design_matrix,
    fit_residual_model,
    partial_correlation,
    save_residual_model,
    spearman_correlation,
)
from atlas.validation.runner import run_all_pairs
from atlas.validation.statistics import percentile_of, summarize


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Quantify structural confounders, build matched percentiles, "
            "and audit near-collisions."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/validation/identity_random_pair_baseline_v1.yaml"),
        help="Baseline config supplying normalization mode and seed.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output") / "validation" / "identity_false_neighbors_v1",
        help="Where to write the audit artifacts.",
    )
    parser.add_argument(
        "--top-fractions",
        type=float,
        nargs="+",
        default=[0.001, 0.0001],
        help="Fractions of the distribution to audit (default: 0.1%%, 0.01%%).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Neighbour records per fraction (default: 50).",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=400_000,
        help="Pairs sampled for regression diagnostics (default: 400,000).",
    )
    return parser


def main() -> int:
    """Run the confounder and false-neighbour audit."""
    args = build_parser().parse_args()
    config = load_config(args.config)

    started = perf_counter()

    corpus = load_corpus_matrix(
        normalization_mode=config.normalization_mode
    )

    if corpus.profile_count < 2:
        print(json.dumps({"success": False, "error": "Corpus too small."}))
        return 1

    pair_indices, scores, _ = run_all_pairs(
        corpus, block_size=int(config.options.get("block_size", 256))
    )

    strata_arrays = name_strata(corpus.profile_names)
    char_lengths = strata_arrays["character_length"]
    token_counts = strata_arrays["token_count"]
    is_ascii = strata_arrays["is_ascii"]

    labels = stratum_keys(
        token_counts=token_counts,
        char_lengths=char_lengths,
        pair_indices=pair_indices,
    )

    # ---- matched percentile index -------------------------------------
    index = build_matched_index(scores=scores, labels=labels)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    save_matched_index(index, args.output_dir / "matched-percentile-index.json")

    global_summary = summarize(scores, bins=200)

    # ---- confounder analysis ------------------------------------------
    left = pair_indices[:, 0]
    right = pair_indices[:, 1]

    length_difference = np.abs(
        char_lengths[left].astype(np.float64)
        - char_lengths[right].astype(np.float64)
    )
    token_difference = np.abs(
        token_counts[left].astype(np.float64)
        - token_counts[right].astype(np.float64)
    )
    total_length = (
        char_lengths[left].astype(np.float64)
        + char_lengths[right].astype(np.float64)
    )

    rng = np.random.default_rng(config.random_seed)
    sample_size = min(args.sample, scores.size)
    sample = rng.choice(scores.size, size=sample_size, replace=False)
    sample.sort()

    confounders = {
        "pearson": {
            "abs_length_difference": float(
                np.corrcoef(length_difference, scores)[0, 1]
            ),
            "abs_token_difference": float(
                np.corrcoef(token_difference, scores)[0, 1]
            ),
            "total_length": float(np.corrcoef(total_length, scores)[0, 1]),
        },
        "spearman_sampled": {
            "abs_length_difference": spearman_correlation(
                length_difference[sample], scores[sample]
            ),
            "abs_token_difference": spearman_correlation(
                token_difference[sample], scores[sample]
            ),
        },
        "partial_sampled": {
            "length_difference_controlling_tokens_and_total": (
                partial_correlation(
                    target=scores[sample],
                    predictor=length_difference[sample],
                    controls=np.column_stack(
                        (
                            token_difference[sample],
                            total_length[sample],
                        )
                    ),
                )
            ),
            "token_difference_controlling_length_and_total": (
                partial_correlation(
                    target=scores[sample],
                    predictor=token_difference[sample],
                    controls=np.column_stack(
                        (
                            length_difference[sample],
                            total_length[sample],
                        )
                    ),
                )
            ),
        },
        "sample_size": int(sample_size),
    }

    # Nonlinear response: mean score at each exact length difference.
    response: list[dict[str, float]] = []

    for difference in range(0, 31):
        selected = scores[length_difference == difference]

        if selected.size >= 100:
            response.append(
                {
                    "length_difference": difference,
                    "pairs": int(selected.size),
                    "mean": float(selected.mean()),
                    "stddev": float(selected.std()),
                }
            )

    confounders["response_by_length_difference"] = response

    # Within-bucket variance: how much score spread survives matching.
    within: list[dict[str, float]] = []
    unique_labels, inverse = np.unique(labels, return_inverse=True)

    for position, label in enumerate(unique_labels):
        selected = scores[inverse == position]

        if selected.size >= 200:
            within.append(
                {
                    "stratum": str(label),
                    "pairs": int(selected.size),
                    "mean": float(selected.mean()),
                    "stddev": float(selected.std()),
                }
            )

    within.sort(key=lambda row: row["pairs"], reverse=True)
    confounders["within_stratum"] = within[:25]

    global_variance = float(scores.var())

    # Pooled within-stratum variance over EVERY pair, weighted by stratum
    # size. An unweighted mean across strata would let a 200-pair stratum
    # count as much as a 1.1-million-pair one and badly misstate the answer.
    stratum_variances = np.array(
        [scores[inverse == position].var() for position in
         range(unique_labels.size)]
    )
    stratum_sizes = np.array(
        [int(np.count_nonzero(inverse == position)) for position in
         range(unique_labels.size)]
    )
    pooled_within_variance = float(
        (stratum_variances * stratum_sizes).sum() / stratum_sizes.sum()
    )

    confounders["global_stddev"] = float(scores.std())
    confounders["global_variance"] = global_variance
    confounders["pooled_within_stratum_variance"] = pooled_within_variance
    confounders["pooled_within_stratum_stddev"] = float(
        np.sqrt(pooled_within_variance)
    )
    # The headline answer to "does signal survive matching": the share of
    # score variance that remains once structurally alike pairs are compared
    # only with each other. Between-stratum variance is what name shape
    # explains; within-stratum variance is what it does not.
    confounders["variance_retained_after_matching"] = (
        pooled_within_variance / global_variance if global_variance > 0 else 0.0
    )
    confounders["variance_explained_by_structure"] = (
        1.0 - pooled_within_variance / global_variance
        if global_variance > 0
        else 0.0
    )

    write_json(confounders, args.output_dir / "confounders.json")

    # ---- residual model ------------------------------------------------
    design = build_design_matrix(
        char_lengths=char_lengths,
        token_counts=token_counts,
        is_ascii=is_ascii,
        pair_indices=pair_indices,
    )
    model = fit_residual_model(scores=scores, design=design)
    save_residual_model(model, args.output_dir / "residual-model.json")

    # ---- false-neighbour audit ------------------------------------------
    audits: dict[str, dict] = {}

    for fraction in args.top_fractions:
        rows = extreme_pairs(
            scores=scores,
            pair_indices=pair_indices,
            fraction=fraction,
            limit=args.limit,
        )

        records = build_neighbor_records(
            corpus=corpus,
            rows=rows,
            scores=scores,
            pair_indices=pair_indices,
            strata=labels,
            char_lengths=char_lengths,
            token_counts=token_counts,
            global_percentile_of=lambda s: percentile_of(global_summary, s),
            matched_percentile_of=index.matched_percentile,
        )

        audits[f"top_{fraction}"] = {
            "fraction": fraction,
            "summary": summarize_false_neighbors(records),
            "records": [record.to_dict() for record in records],
        }

    write_json({"audits": audits}, args.output_dir / "false-neighbors.json")

    provenance = build_provenance(
        config,
        profile_count=corpus.profile_count,
        pair_count=int(scores.size),
        block_size=int(config.options.get("block_size", 256)),
    ).to_dict()
    write_json(provenance, args.output_dir / "provenance.json")

    headline = audits[f"top_{args.top_fractions[0]}"]["summary"]

    print(
        json.dumps(
            {
                "success": True,
                "output_dir": str(args.output_dir),
                "pairs": int(scores.size),
                "matched_index": index.coverage(),
                "confounders": {
                    "pearson_length": confounders["pearson"][
                        "abs_length_difference"
                    ],
                    "spearman_length": confounders["spearman_sampled"][
                        "abs_length_difference"
                    ],
                    "partial_length": confounders["partial_sampled"][
                        "length_difference_controlling_tokens_and_total"
                    ],
                },
                "residual_model": {
                    "r_squared": model.r_squared,
                    "residual_stddev": model.residual_stddev,
                },
                "variance_retained_after_matching": confounders[
                    "variance_retained_after_matching"
                ],
                "false_neighbors_top_0.1pct": {
                    "examined": headline["count"],
                    "explained_by_structure": headline[
                        "explained_by_structure"
                    ],
                    "still_extreme_when_matched": headline[
                        "still_extreme_when_matched"
                    ],
                    "mean_length_difference": headline[
                        "mean_length_difference"
                    ],
                },
                "elapsed_seconds": round(perf_counter() - started, 2),
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
