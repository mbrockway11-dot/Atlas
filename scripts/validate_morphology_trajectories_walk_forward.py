"""Walk-forward validate leading morphology trajectories."""

from __future__ import annotations

import argparse

from atlas.investment.morphology_intelligence.trajectory import (
    MorphologyTrajectoryConfig,
    load_trajectory_assignments,
)
from atlas.investment.morphology_intelligence.trajectory_walk_forward import (
    TrajectoryWalkForwardConfig,
    run_trajectory_walk_forward,
    summarize_walk_forward,
    write_walk_forward_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--assignments",
        required=True,
    )

    parser.add_argument(
        "--output",
        default=(
            "output/"
            "investment_morphology_trajectory_walk_forward"
        ),
    )

    parser.add_argument(
        "--fold-count",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--minimum-training-observations",
        type=int,
        default=50,
    )

    parser.add_argument(
        "--minimum-test-observations",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--initial-training-fraction",
        type=float,
        default=0.50,
    )

    args = parser.parse_args()

    trajectory_config = (
        MorphologyTrajectoryConfig(
            sequence_lengths=(3, 5),
            outcome_horizons=(
                8,
                32,
            ),
            minimum_observations=2,
            confidence_target=500,
            stride=1,
            maximum_gap_multiple=3.0,
            risk_penalty=0.50,
        )
    )

    validation_config = (
        TrajectoryWalkForwardConfig(
            fold_count=args.fold_count,
            minimum_training_observations=(
                args.minimum_training_observations
            ),
            minimum_test_observations=(
                args.minimum_test_observations
            ),
            initial_training_fraction=(
                args.initial_training_fraction
            ),
            risk_penalty=0.50,
        )
    )

    assignments = (
        load_trajectory_assignments(
            args.assignments,
            config=trajectory_config,
        )
    )

    folds = run_trajectory_walk_forward(
        assignments,
        trajectory_config=(
            trajectory_config
        ),
        validation_config=(
            validation_config
        ),
    )

    summary = summarize_walk_forward(
        folds
    )

    outputs = write_walk_forward_outputs(
        folds=folds,
        summary=summary,
        trajectory_config=(
            trajectory_config
        ),
        validation_config=(
            validation_config
        ),
        output_dir=args.output,
    )

    print(
        "=== TRAJECTORY WALK-FORWARD VALIDATION ==="
    )

    print(
        f"fold_rows={len(folds)}"
    )

    print(
        f"candidates={len(summary)}"
    )

    print(
        "promotion_candidates="
        f"{int(summary['promotion_candidate'].astype(bool).sum())}"
    )

    for row in summary.itertuples(
        index=False
    ):
        print(
            f"{row.candidate_id}: "
            f"passed={row.passed_fold_count}/"
            f"{row.validated_fold_count} "
            f"pass_rate={row.fold_pass_rate:.3f} "
            f"test_return={row.weighted_test_mean_return:.6f} "
            f"test_edge={row.weighted_test_risk_adjusted_edge:.6f} "
            f"promotion={row.promotion_candidate}"
        )

    for name, path in outputs.items():
        print(f"{name}={path}")


if __name__ == "__main__":
    main()
