"""Run Morphology Field Walk-Forward Validator V1."""

from __future__ import annotations

import argparse

from atlas.investment.morphology_intelligence.field_walk_forward import (
    FieldWalkForwardConfig,
    load_walk_forward_motion,
    load_walk_forward_outcomes,
    run_field_walk_forward,
    summarize_field_validation,
    write_field_walk_forward_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--motion",
        required=True,
    )

    parser.add_argument(
        "--assignments",
        required=True,
    )

    parser.add_argument(
        "--output",
        default=(
            "output/"
            "investment_morphology_field_walk_forward"
        ),
    )

    parser.add_argument(
        "--training-days",
        type=int,
        default=180,
    )

    parser.add_argument(
        "--test-days",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--step-days",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--horizon-bars",
        type=int,
        default=16,
    )

    parser.add_argument(
        "--embargo-bars",
        type=int,
        default=96,
    )

    parser.add_argument(
        "--grid-bins",
        type=int,
        default=24,
    )

    parser.add_argument(
        "--minimum-cell-observations",
        type=int,
        default=15,
    )

    parser.add_argument(
        "--minimum-training-timestamps",
        type=int,
        default=5000,
    )

    parser.add_argument(
        "--minimum-test-timestamps",
        type=int,
        default=500,
    )

    parser.add_argument(
        "--minimum-test-observations",
        type=int,
        default=30,
    )

    args = parser.parse_args()

    config = FieldWalkForwardConfig(
        training_days=args.training_days,
        test_days=args.test_days,
        step_days=args.step_days,
        horizon_bars=args.horizon_bars,
        embargo_bars=args.embargo_bars,
        grid_bins=args.grid_bins,
        minimum_cell_observations=(
            args.minimum_cell_observations
        ),
        minimum_training_timestamps=(
            args.minimum_training_timestamps
        ),
        minimum_test_timestamps=(
            args.minimum_test_timestamps
        ),
        minimum_test_observations=(
            args.minimum_test_observations
        ),
    )

    motion = load_walk_forward_motion(
        args.motion
    )

    outcomes = load_walk_forward_outcomes(
        args.assignments,
        horizon_bars=(
            config.horizon_bars
        ),
    )

    scores, evaluations = (
        run_field_walk_forward(
            motion=motion,
            outcomes=outcomes,
            config=config,
        )
    )

    summary = summarize_field_validation(
        evaluations
    )

    outputs = (
        write_field_walk_forward_outputs(
            scores=scores,
            evaluations=evaluations,
            summary=summary,
            config=config,
            output_dir=args.output,
        )
    )

    print(
        "=== MORPHOLOGY FIELD WALK-FORWARD V1 ==="
    )

    print(
        f"scored_rows={len(scores)}"
    )

    print(
        "fold_evaluation_rows="
        f"{len(evaluations)}"
    )

    print(
        f"summary_rows={len(summary)}"
    )

    print(
        "research_candidates="
        f"{int(summary['research_candidate'].astype(bool).sum()) if not summary.empty else 0}"
    )

    if not summary.empty:
        for row in (
            summary.head(20)
            .itertuples(index=False)
        ):
            print(
                f"{row.asset} "
                f"{row.direction} "
                f"{row.condition_name}: "
                f"folds={row.eligible_fold_count} "
                f"n={row.total_observations} "
                f"return={row.weighted_mean_return:.6f} "
                f"uplift={row.weighted_mean_return_uplift:.6f} "
                f"uplift_rate={row.positive_uplift_fold_rate:.3f} "
                f"candidate={row.research_candidate}"
            )

    for name, path in outputs.items():
        print(f"{name}={path}")


if __name__ == "__main__":
    main()
