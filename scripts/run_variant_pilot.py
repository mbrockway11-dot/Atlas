"""Dual-metric same-person variant pilot.

Scores genuine variants against transformation-conditioned controls under
both the canonical metric (cosine) and the leading research metric (centered
cosine), and reports them side by side. The production metric is not changed
here; the pilot exists to decide whether centered cosine improves *variant
discrimination*, not merely geometric resolution.

The principal result for each class is separation from its **primary null** --
a control that has undergone the same structural transformation as the
variant. Comparison against the global population is reported too, but it is
not the test: the perturbation study showed that structural change alone
moves scores further than most variants do.

    python scripts/run_variant_pilot.py
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
from atlas.validation.matching import (
    build_matched_index,
    stratum_keys,
)
from atlas.validation.metrics import METRICS_BY_NAME, separation
from atlas.validation.models import load_config
from atlas.validation.nulls import PRIMARY_NULL, generate_nulls
from atlas.validation.runner import unit_normalize
from atlas.validation.statistics import percentile_of, summarize
from atlas.validation.variant_dataset import build_pilot_dataset
from atlas.validation.variants import VariantClass, validate_dataset


CANONICAL_METRIC = "cosine"
RESEARCH_METRIC = "centered_cosine"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Run the dual-metric same-person variant pilot."
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
        default=Path("output") / "validation" / "name_variant_pilot_v1",
    )
    parser.add_argument(
        "--controls-per-null",
        type=int,
        default=5,
        help="Controls generated per null model per pair (default: 5).",
    )
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=10_000,
        help="Bootstrap iterations (default: 10,000).",
    )
    return parser


def _score_pairs(
    pairs: list[tuple[np.ndarray, np.ndarray]],
    metric_name: str,
    corpus_matrix: np.ndarray,
) -> np.ndarray:
    """Score aligned vector pairs under a metric, centered on the corpus.

    Centering is estimated from the corpus so that a pilot score is on the
    same scale as the population baseline. Estimating it from the handful of
    pilot rows would make the numbers incomparable.
    """
    if not pairs:
        return np.array([])

    metric = METRICS_BY_NAME[metric_name]
    stacked = np.vstack(
        [corpus_matrix] + [np.vstack(pair) for pair in pairs]
    )
    scores = metric.pairwise(stacked)

    offset = corpus_matrix.shape[0]

    return np.array(
        [
            scores[offset + 2 * index, offset + 2 * index + 1]
            for index in range(len(pairs))
        ]
    )


def _bootstrap_difference(
    positive: np.ndarray,
    control: np.ndarray,
    *,
    iterations: int,
    seed: int,
) -> dict[str, float | bool]:
    """Return a bootstrap CI for the positive-minus-control mean difference."""
    if positive.size == 0 or control.size == 0:
        return {"difference": 0.0, "lower": 0.0, "upper": 0.0,
                "includes_zero": True}

    rng = np.random.default_rng(seed)
    differences = np.empty(iterations, dtype=np.float64)

    for index in range(iterations):
        differences[index] = (
            positive[rng.integers(0, positive.size, positive.size)].mean()
            - control[rng.integers(0, control.size, control.size)].mean()
        )

    lower = float(np.percentile(differences, 2.5))
    upper = float(np.percentile(differences, 97.5))

    return {
        "difference": float(positive.mean() - control.mean()),
        "lower": lower,
        "upper": upper,
        "includes_zero": bool(lower <= 0.0 <= upper),
    }


def _auc(positive: np.ndarray, control: np.ndarray) -> float:
    """Return the probability a random positive outranks a random control."""
    if positive.size == 0 or control.size == 0:
        return 0.5

    return float((positive[:, None] > control[None, :]).mean())


def main() -> int:
    """Run the pilot."""
    args = build_parser().parse_args()
    config = load_config(args.config)
    started = perf_counter()

    corpus = load_corpus_matrix(normalization_mode=config.normalization_mode)
    layout = build_feature_layout()
    corpus_names = list(corpus.profile_names)

    dataset = build_pilot_dataset(corpus_names)
    validation = validate_dataset(dataset)

    if not validation["valid"]:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "Dataset failed validation.",
                    "problems": validation["problems"][:10],
                },
                indent=2,
            )
        )
        return 1

    # Global reference distributions under both metrics.
    references: dict[str, dict] = {}

    for metric_name in (CANONICAL_METRIC, RESEARCH_METRIC):
        metric = METRICS_BY_NAME[metric_name]
        matrix = metric.pairwise(corpus.matrix)
        rows, columns = np.triu_indices(corpus.profile_count, k=1)
        references[metric_name] = {
            "summary": summarize(matrix[rows, columns], bins=200),
        }

    # ---- score positives and their conditioned nulls ---------------------
    positive_rows: list[dict] = []
    scored: dict[str, dict[str, list]] = {
        metric: {"positive": [], "nulls": {}}
        for metric in (CANONICAL_METRIC, RESEARCH_METRIC)
    }

    positive_vector_pairs: list[tuple[np.ndarray, np.ndarray]] = []
    positive_meta: list[dict] = []
    null_vector_pairs: dict[str, list[tuple[np.ndarray, np.ndarray]]] = {}
    null_meta: dict[str, list[dict]] = {}

    for pair in dataset:
        canonical_vector = vector_for_name(pair.canonical_name, layout=layout)
        variant_vector = vector_for_name(pair.variant_name, layout=layout)

        if canonical_vector is None or variant_vector is None:
            continue

        positive_vector_pairs.append((canonical_vector, variant_vector))
        positive_meta.append(
            {**pair.to_dict(), "variant_class": pair.variant_class.value}
        )

        controls = generate_nulls(
            canonical=pair.canonical_name,
            variant=pair.variant_name,
            variant_class=pair.variant_class,
            corpus_names=corpus_names,
            controls_per_null=args.controls_per_null,
            seed=config.random_seed,
        )

        for null_name, control_names in controls.items():
            key = f"{pair.variant_class.value}|{null_name}"
            null_vector_pairs.setdefault(key, [])
            null_meta.setdefault(key, [])

            for control_name in control_names:
                control_vector = vector_for_name(control_name, layout=layout)

                if control_vector is None:
                    continue

                null_vector_pairs[key].append(
                    (canonical_vector, control_vector)
                )
                null_meta[key].append(
                    {
                        "entity_id": pair.entity_id,
                        "control_name": control_name,
                        "null_model": null_name,
                        "variant_class": pair.variant_class.value,
                    }
                )

    results: dict[str, dict] = {}

    for metric_name in (CANONICAL_METRIC, RESEARCH_METRIC):
        positives = _score_pairs(
            positive_vector_pairs, metric_name, corpus.matrix
        )
        null_scores = {
            key: _score_pairs(pairs, metric_name, corpus.matrix)
            for key, pairs in null_vector_pairs.items()
        }

        summary = references[metric_name]["summary"]
        by_class: dict[str, dict] = {}

        for variant_class in VariantClass:
            selected = np.array(
                [
                    index
                    for index, meta in enumerate(positive_meta)
                    if meta["variant_class"] == variant_class.value
                ]
            )

            if selected.size == 0:
                continue

            class_positives = positives[selected]
            primary = PRIMARY_NULL[variant_class]
            primary_key = f"{variant_class.value}|{primary}"
            primary_scores = null_scores.get(primary_key, np.array([]))

            null_comparisons: dict[str, dict] = {}

            for key, values in null_scores.items():
                if not key.startswith(f"{variant_class.value}|"):
                    continue

                null_name = key.split("|", 1)[1]
                null_comparisons[null_name] = {
                    "null_samples": int(values.size),
                    "null_mean": float(values.mean()) if values.size else None,
                    **separation(class_positives, values),
                    "auc": _auc(class_positives, values),
                    "bootstrap": _bootstrap_difference(
                        class_positives,
                        values,
                        iterations=args.bootstrap,
                        seed=config.random_seed,
                    ),
                    "is_primary": null_name == primary,
                }

            by_class[variant_class.value] = {
                "positive_samples": int(class_positives.size),
                "positive_mean": float(class_positives.mean()),
                "positive_median": float(np.median(class_positives)),
                "positive_stddev": float(class_positives.std()),
                "global_percentile_of_mean": float(
                    percentile_of(summary, float(class_positives.mean()))
                ),
                "primary_null": primary,
                "nulls": null_comparisons,
                # The principal result: separation from the conditioned null.
                "primary_result": null_comparisons.get(primary, {}),
            }

        results[metric_name] = {
            "population_mean": summary.mean,
            "population_stddev": summary.stddev,
            "by_class": by_class,
        }

    # ---- metric comparison ------------------------------------------------
    comparison_rows: list[dict] = []

    for variant_class in VariantClass:
        key = variant_class.value
        canonical = results[CANONICAL_METRIC]["by_class"].get(key)
        research = results[RESEARCH_METRIC]["by_class"].get(key)

        if not canonical or not research:
            continue

        comparison_rows.append(
            {
                "variant_class": key,
                "primary_null": canonical["primary_null"],
                "cosine_d": canonical["primary_result"].get("cohens_d"),
                "centered_cosine_d": research["primary_result"].get(
                    "cohens_d"
                ),
                "cosine_auc": canonical["primary_result"].get("auc"),
                "centered_cosine_auc": research["primary_result"].get("auc"),
                "cosine_ci_includes_zero": canonical["primary_result"]
                .get("bootstrap", {})
                .get("includes_zero"),
                "centered_cosine_ci_includes_zero": research["primary_result"]
                .get("bootstrap", {})
                .get("includes_zero"),
            }
        )

    improved = [
        row
        for row in comparison_rows
        if row["centered_cosine_d"] is not None
        and row["cosine_d"] is not None
        and row["centered_cosine_d"] > row["cosine_d"]
    ]

    args.output_dir.mkdir(parents=True, exist_ok=True)

    write_json(
        {"dataset_validation": validation,
         "rows": [meta for meta in positive_meta]},
        args.output_dir / "dataset_snapshot.json",
    )
    write_json(results[CANONICAL_METRIC], args.output_dir / "cosine_summary.json")
    write_json(
        results[RESEARCH_METRIC],
        args.output_dir / "centered_cosine_summary.json",
    )
    write_json(
        {
            "canonical_metric": CANONICAL_METRIC,
            "research_metric": RESEARCH_METRIC,
            "by_class": comparison_rows,
            "classes_improved_by_centering": [
                row["variant_class"] for row in improved
            ],
            "decision_gate": {
                "improves_two_or_more_classes": len(improved) >= 2,
                "note": (
                    "Centered cosine becomes the default research metric "
                    "only if it improves conditioned effect size in at least "
                    "two substantive classes without worsening false "
                    "positives or confounding."
                ),
            },
        },
        args.output_dir / "metric_comparison.json",
    )
    write_json(
        build_provenance(
            config,
            profile_count=corpus.profile_count,
            pair_count=len(positive_meta),
            block_size=int(config.options.get("block_size", 256)),
        ).to_dict(),
        args.output_dir / "provenance.json",
    )

    print(
        json.dumps(
            {
                "success": True,
                "dataset": {
                    "pairs": validation["total_pairs"],
                    "by_class": validation["by_class"],
                    "by_confidence": validation["by_confidence"],
                },
                "scored_positives": len(positive_meta),
                "primary_results": {
                    metric: {
                        key: {
                            "n": body["positive_samples"],
                            "mean": round(body["positive_mean"], 5),
                            "primary_null": body["primary_null"],
                            "null_mean": round(
                                body["primary_result"].get("null_mean") or 0.0,
                                5,
                            ),
                            "d": round(
                                body["primary_result"].get("cohens_d") or 0.0,
                                3,
                            ),
                            "auc": round(
                                body["primary_result"].get("auc") or 0.0, 3
                            ),
                            "ci_includes_zero": body["primary_result"]
                            .get("bootstrap", {})
                            .get("includes_zero"),
                        }
                        for key, body in results[metric]["by_class"].items()
                    }
                    for metric in (CANONICAL_METRIC, RESEARCH_METRIC)
                },
                "classes_improved_by_centering": [
                    row["variant_class"] for row in improved
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
