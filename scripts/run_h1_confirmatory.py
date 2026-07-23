"""Confirmatory test of H1 on a held-out orthographic cohort.

Tests one pre-registered hypothesis against a cohort disjoint from the pilot,
using only pairs derived by construction. Results are reported per subclass,
with A1 shown but excluded from the endpoint: the encoder is exactly
invariant to case and spacing, so scoring 1.0 there is circular.

    python scripts/run_h1_confirmatory.py
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
    vector_for_name,
)
from atlas.validation.h1_confirmatory import build_h1_confirmatory_dataset
from atlas.validation.metrics import METRICS_BY_NAME, separation
from atlas.validation.models import load_config
from atlas.validation.nulls import NULL_GENERATORS_BY_NAME
from atlas.validation.variant_dataset import build_pilot_dataset
from atlas.validation.variants import (
    CONFIRMATORY_STATES,
    SUBCLASS_ROLE,
    OrthographicSubclass,
)


PRIMARY_NULL = "edit_and_length_matched_mutation"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Run the pre-registered H1 confirmatory experiment."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(
            "configs/validation/h1_orthographic_confirmatory_v1.yaml"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output")
        / "validation"
        / "h1_orthographic_confirmatory_v1",
    )
    return parser


def _score(
    pairs: list[tuple[np.ndarray, np.ndarray]],
    metric_name: str,
    corpus_matrix: np.ndarray,
) -> np.ndarray:
    """Score aligned vector pairs under a metric, centered on the corpus."""
    if not pairs:
        return np.array([])

    metric = METRICS_BY_NAME[metric_name]
    stacked = np.vstack([corpus_matrix] + [np.vstack(p) for p in pairs])
    scores = metric.pairwise(stacked)
    offset = corpus_matrix.shape[0]

    return np.array(
        [scores[offset + 2 * i, offset + 2 * i + 1] for i in range(len(pairs))]
    )


def _bootstrap_auc(
    positive: np.ndarray,
    control: np.ndarray,
    *,
    iterations: int,
    seed: int,
) -> dict[str, float | bool]:
    """Return the conditioned AUC with a bootstrap interval."""
    if positive.size == 0 or control.size == 0:
        return {"auc": 0.5, "lower": 0.5, "upper": 0.5, "excludes_half": False}

    observed = float((positive[:, None] > control[None, :]).mean())

    rng = np.random.default_rng(seed)
    draws = np.empty(iterations, dtype=np.float64)

    for index in range(iterations):
        a = positive[rng.integers(0, positive.size, positive.size)]
        b = control[rng.integers(0, control.size, control.size)]
        draws[index] = (a[:, None] > b[None, :]).mean()

    lower = float(np.percentile(draws, 2.5))
    upper = float(np.percentile(draws, 97.5))

    return {
        "auc": observed,
        "lower": lower,
        "upper": upper,
        "excludes_half": bool(lower > 0.5 or upper < 0.5),
        # H1 is directional: it predicts positives score HIGHER than
        # controls. An interval excluding 0.5 from BELOW is a significant
        # result in the opposite direction, and must never be read as
        # support. Keeping these separate is the difference between
        # confirming a hypothesis and merely finding an effect.
        "supports_hypothesis": bool(lower > 0.5),
        "contradicts_hypothesis": bool(upper < 0.5),
    }


def main() -> int:
    """Run the confirmatory experiment."""
    args = build_parser().parse_args()
    config = load_config(args.config)
    options = config.options
    started = perf_counter()

    canonical_metric = str(options.get("canonical_metric", "cosine"))
    research_metric = str(options.get("research_metric", "centered_cosine"))

    corpus = load_corpus_matrix(normalization_mode=config.normalization_mode)
    layout = build_feature_layout()
    corpus_names = list(corpus.profile_names)

    # Hold out every name the pilot touched.
    pilot_names = {
        pair.canonical_name.strip().lower()
        for pair in build_pilot_dataset(corpus_names)
    }

    dataset = build_h1_confirmatory_dataset(
        corpus_names,
        excluded_names=sorted(pilot_names),
        target_per_subclass=int(options.get("target_per_subclass", 50)),
        seed=config.random_seed,
    )

    inadmissible = [
        pair
        for pair in dataset
        if pair.source_confidence not in CONFIRMATORY_STATES
    ]

    if inadmissible:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": (
                        f"{len(inadmissible)} pair(s) are not admissible in a "
                        "confirmatory study."
                    ),
                },
                indent=2,
            )
        )
        return 1

    generator = NULL_GENERATORS_BY_NAME[PRIMARY_NULL]
    controls_per_null = int(options.get("controls_per_null", 5))

    positives: dict[str, list[tuple[np.ndarray, np.ndarray]]] = {}
    controls: dict[str, list[tuple[np.ndarray, np.ndarray]]] = {}
    overlap_with_pilot = 0

    for pair in dataset:
        if pair.canonical_name.strip().lower() in pilot_names:
            overlap_with_pilot += 1
            continue

        canonical_vector = vector_for_name(pair.canonical_name, layout=layout)
        variant_vector = vector_for_name(pair.variant_name, layout=layout)

        if canonical_vector is None or variant_vector is None:
            continue

        subclass = pair.subclass.value
        positives.setdefault(subclass, []).append(
            (canonical_vector, variant_vector)
        )

        for attempt in range(controls_per_null):
            rng = np.random.default_rng(
                abs(hash((pair.entity_id, attempt))) % (2**32)
            )
            control_name = generator.generate(
                pair.canonical_name, pair.variant_name, corpus_names, rng
            )

            if not control_name:
                continue

            control_vector = vector_for_name(control_name, layout=layout)

            if control_vector is not None:
                controls.setdefault(subclass, []).append(
                    (canonical_vector, control_vector)
                )

    results: dict[str, dict] = {}

    for metric_name in (canonical_metric, research_metric):
        by_subclass: dict[str, dict] = {}

        for subclass in OrthographicSubclass:
            key = subclass.value

            if key not in positives:
                continue

            positive_scores = _score(
                positives[key], metric_name, corpus.matrix
            )
            control_scores = _score(
                controls.get(key, []), metric_name, corpus.matrix
            )

            endpoint = _bootstrap_auc(
                positive_scores,
                control_scores,
                iterations=config.bootstrap_iterations or 10_000,
                seed=config.random_seed,
            )

            by_subclass[key] = {
                "role": SUBCLASS_ROLE[subclass],
                "in_endpoint": SUBCLASS_ROLE[subclass] == "substantive",
                "positive_samples": int(positive_scores.size),
                "control_samples": int(control_scores.size),
                "positive_mean": float(positive_scores.mean())
                if positive_scores.size
                else None,
                "control_mean": float(control_scores.mean())
                if control_scores.size
                else None,
                "conditioned_auc": endpoint,
                **separation(positive_scores, control_scores),
            }

        substantive = [
            body for body in by_subclass.values() if body["in_endpoint"]
        ]

        results[metric_name] = {
            "by_subclass": by_subclass,
            "mean_conditioned_auc": (
                float(
                    np.mean(
                        [b["conditioned_auc"]["auc"] for b in substantive]
                    )
                )
                if substantive
                else None
            ),
            "any_substantive_endpoint_supports": any(
                b["conditioned_auc"]["supports_hypothesis"]
                for b in substantive
            ),
            "any_substantive_endpoint_contradicts": any(
                b["conditioned_auc"]["contradicts_hypothesis"]
                for b in substantive
            ),
        }

    canonical_results = results[canonical_metric]

    if canonical_results["any_substantive_endpoint_supports"]:
        verdict = "H1_supported"
    elif canonical_results["any_substantive_endpoint_contradicts"]:
        verdict = "H1_contradicted"
    else:
        verdict = "H1_not_supported"

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        {
            "rows": [pair.to_dict() for pair in dataset],
            "held_out_from": options.get("held_out_from"),
            "overlap_with_pilot": overlap_with_pilot,
            "admissible_states": sorted(
                state.value for state in CONFIRMATORY_STATES
            ),
        },
        args.output_dir / "dataset_snapshot.json",
    )
    write_json(config.to_dict(), args.output_dir / "experiment.json")
    write_json(results[canonical_metric], args.output_dir / "cosine_summary.json")
    write_json(
        results[research_metric],
        args.output_dir / "centered_cosine_summary.json",
    )
    write_json(
        {
            "verdict": verdict,
            "primary_endpoint": options.get("primary_endpoint"),
            "canonical_metric": canonical_metric,
            "research_metric": research_metric,
            "minimum_detectable_effect": options.get(
                "minimum_detectable_effect"
            ),
            "note": (
                "A1 is reported but excluded from the endpoint: the encoder "
                "is exactly invariant to case and spacing, so a score of 1.0 "
                "is true by construction, not evidence of variant "
                "recognition."
            ),
        },
        args.output_dir / "verdict.json",
    )
    write_json(
        build_provenance(
            config,
            profile_count=corpus.profile_count,
            pair_count=sum(len(v) for v in positives.values()),
            block_size=256,
        ).to_dict(),
        args.output_dir / "provenance.json",
    )

    print(
        json.dumps(
            {
                "success": True,
                "verdict": verdict,
                "dataset_pairs": len(dataset),
                "overlap_with_pilot": overlap_with_pilot,
                "results": {
                    metric: {
                        key: {
                            "role": body["role"],
                            "n_pos": body["positive_samples"],
                            "n_ctrl": body["control_samples"],
                            "pos_mean": round(body["positive_mean"] or 0.0, 5),
                            "ctrl_mean": round(body["control_mean"] or 0.0, 5),
                            "auc": round(body["conditioned_auc"]["auc"], 3),
                            "auc_ci": [
                                round(body["conditioned_auc"]["lower"], 3),
                                round(body["conditioned_auc"]["upper"], 3),
                            ],
                            "supports": body["conditioned_auc"][
                                "supports_hypothesis"
                            ],
                            "contradicts": body["conditioned_auc"][
                                "contradicts_hypothesis"
                            ],
                            "d": round(body["cohens_d"], 3),
                        }
                        for key, body in results[metric]["by_subclass"].items()
                    }
                    for metric in (canonical_metric, research_metric)
                },
                "output_dir": str(args.output_dir),
                "elapsed_seconds": round(perf_counter() - started, 2),
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
