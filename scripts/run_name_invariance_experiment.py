"""Test declared invariance expectations against measured behaviour.

Each transformation carries a prediction made in advance -- invariant,
near-invariant, variant, or ambiguous -- so this experiment tests a
hypothesis rather than describing whatever happened. Transformations whose
measured behaviour contradicts their declared expectation are reported as
violations, which is the point of declaring them.

    python scripts/run_name_invariance_experiment.py
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
    cosine,
    load_corpus_matrix,
    vector_for_name,
)
from atlas.validation.matching import (
    length_difference_bucket,
    load_matched_index,
)
from atlas.validation.models import load_config
from atlas.validation.perturbations import (
    INVARIANCE_TRANSFORMATIONS,
    Expectation,
)
from atlas.validation.runner import run_all_pairs
from atlas.validation.statistics import percentile_of, summarize


# What each declared expectation predicts about similarity. Deliberately
# generous bands: the test is whether behaviour lands in the declared class,
# not whether it hits a precise number.
#
# Upper bounds carry a tolerance because a cosine of two nearly-parallel
# float vectors can land marginally above 1.0. Without it, a perfectly
# invariant transformation scoring 1.0000000000000002 would be reported as
# violating an invariance expectation -- the opposite of the truth.
FLOAT_TOLERANCE = 1e-9

EXPECTATION_BANDS = {
    Expectation.INVARIANT: (1.0 - FLOAT_TOLERANCE, 1.0 + FLOAT_TOLERANCE),
    Expectation.NEAR_INVARIANT: (0.995, 1.0 + FLOAT_TOLERANCE),
    Expectation.VARIANT: (0.0, 1.0 - 1e-4),
    Expectation.AMBIGUOUS: (0.0, 1.0 + FLOAT_TOLERANCE),
}


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Run the name-invariance experiment."
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
        default=Path("output") / "validation" / "identity_name_invariance_v1",
    )
    parser.add_argument(
        "--sample-names",
        type=int,
        default=300,
        help="Corpus names to transform (default: 300).",
    )
    parser.add_argument(
        "--matched-index",
        type=Path,
        default=Path("output")
        / "validation"
        / "identity_false_neighbors_v1"
        / "matched-percentile-index.json",
    )
    return parser


def main() -> int:
    """Run the invariance suite."""
    args = build_parser().parse_args()
    config = load_config(args.config)
    started = perf_counter()

    corpus = load_corpus_matrix(normalization_mode=config.normalization_mode)
    layout = build_feature_layout()

    rng = np.random.default_rng(config.random_seed)
    sample_size = min(args.sample_names, corpus.profile_count)
    chosen = rng.choice(corpus.profile_count, size=sample_size, replace=False)
    names = [corpus.profile_names[int(index)] for index in chosen]

    # Global reference distribution, for percentile context.
    _, all_scores, _ = run_all_pairs(corpus, block_size=256)
    global_summary = summarize(all_scores, bins=200)

    matched_index = (
        load_matched_index(args.matched_index)
        if args.matched_index.is_file()
        else None
    )

    baseline_vectors: dict[str, np.ndarray] = {}

    for name in names:
        vector = vector_for_name(name, layout=layout)

        if vector is not None:
            baseline_vectors[name] = vector

    results: list[dict] = []

    for transformation in INVARIANCE_TRANSFORMATIONS:
        scores: list[float] = []
        length_deltas: list[int] = []
        token_deltas: list[int] = []
        unchanged = 0
        failures = 0

        for name, original_vector in baseline_vectors.items():
            try:
                transformed = transformation.apply(name)
            except Exception:  # noqa: BLE001 - a failed transform is a skip
                failures += 1
                continue

            if transformed == name:
                unchanged += 1
                continue

            vector = vector_for_name(transformed, layout=layout)

            if vector is None:
                failures += 1
                continue

            scores.append(cosine(original_vector, vector))
            length_deltas.append(
                len(transformed.replace(" ", "")) - len(name.replace(" ", ""))
            )
            token_deltas.append(
                len(transformed.split()) - len(name.split())
            )

        if not scores:
            results.append(
                {
                    "transformation": transformation.name,
                    "expectation": transformation.expectation.value,
                    "rationale": transformation.rationale,
                    "applicable_names": 0,
                    "unchanged_names": unchanged,
                    "failures": failures,
                    "verdict": "not_applicable",
                }
            )
            continue

        values = np.array(scores, dtype=np.float64)
        low, high = EXPECTATION_BANDS[transformation.expectation]
        mean = float(values.mean())

        # A transformation meets its expectation when the bulk of its
        # outcomes fall in the declared band.
        in_band = float(
            np.count_nonzero((values >= low) & (values <= high)) / values.size
        )

        exactly_invariant = bool(values.min() >= 1.0 - FLOAT_TOLERANCE)

        if transformation.expectation is Expectation.AMBIGUOUS:
            verdict = (
                "invariant_in_practice"
                if exactly_invariant
                else "variant_in_practice"
            )
        elif in_band < 0.95:
            verdict = "violates_expectation"
        elif (
            transformation.expectation is Expectation.NEAR_INVARIANT
            and exactly_invariant
        ):
            # Stronger than predicted, not a failure -- worth naming so the
            # expectation can be tightened next time.
            verdict = "exceeds_expectation"
        else:
            verdict = "meets_expectation"

        results.append(
            {
                "transformation": transformation.name,
                "expectation": transformation.expectation.value,
                "rationale": transformation.rationale,
                "preserves_length": transformation.preserves_length,
                "applicable_names": int(values.size),
                "unchanged_names": unchanged,
                "failures": failures,
                "mean_similarity": mean,
                "median_similarity": float(np.median(values)),
                "min_similarity": float(values.min()),
                "max_similarity": float(values.max()),
                "fraction_exactly_identical": float(
                    np.count_nonzero(values >= 1.0 - FLOAT_TOLERANCE)
                    / values.size
                ),
                "fraction_in_expected_band": in_band,
                "global_percentile_of_mean": float(
                    percentile_of(global_summary, mean)
                ),
                "matched_percentile_of_mean": (
                    float(
                        matched_index.matched_percentile(
                            mean,
                            f"2+2|len:{length_difference_bucket(int(abs(np.mean(length_deltas))))}",
                        )
                    )
                    if matched_index is not None
                    else None
                ),
                "mean_length_change": float(np.mean(length_deltas)),
                "mean_token_change": float(np.mean(token_deltas)),
                "verdict": verdict,
            }
        )

    violations = [r for r in results if r.get("verdict") == "violates_expectation"]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json({"transformations": results}, args.output_dir / "invariance.json")
    write_json(
        build_provenance(
            config,
            profile_count=len(baseline_vectors),
            pair_count=len(baseline_vectors) * len(INVARIANCE_TRANSFORMATIONS),
            block_size=int(config.options.get("block_size", 256)),
        ).to_dict(),
        args.output_dir / "provenance.json",
    )

    print(
        json.dumps(
            {
                "success": True,
                "names_tested": len(baseline_vectors),
                "transformations": len(results),
                "violations": [v["transformation"] for v in violations],
                "summary": [
                    {
                        "transformation": r["transformation"],
                        "expectation": r["expectation"],
                        "mean": round(r.get("mean_similarity", 0.0), 6),
                        "min": round(r.get("min_similarity", 0.0), 6),
                        "identical_fraction": round(
                            r.get("fraction_exactly_identical", 0.0), 4
                        ),
                        "verdict": r["verdict"],
                    }
                    for r in results
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
