from __future__ import annotations

import pandas as pd

from atlas.investment.morphology_intelligence.trajectory import (
    MorphologyTrajectoryConfig,
    build_latest_trajectory_windows,
    build_timestamp_morphology,
)
from atlas.investment.morphology_intelligence.trajectory_walk_forward import (
    TrajectoryWalkForwardConfig,
    build_walk_forward_boundaries,
    run_trajectory_walk_forward,
    summarize_walk_forward,
)


def _assignments(
    periods: int = 400,
) -> pd.DataFrame:
    timestamps = pd.date_range(
        "2025-01-01",
        periods=periods,
        freq="15min",
        tz="UTC",
    )

    pattern = [
        5,
        7,
        3,
        8,
        8,
        8,
        3,
        8,
    ]

    rows = []

    for index, timestamp in enumerate(
        timestamps
    ):
        cluster_id = pattern[
            index % len(pattern)
        ]

        for asset in (
            "BTC",
            "ETH",
            "SOL",
        ):
            base = (
                0.01
                if asset == "SOL"
                else 0.006
            )

            rows.append({
                "timestamp":
                    timestamp,
                "asset":
                    asset,
                "morphology_cluster_id":
                    cluster_id,
                "morphology_cluster":
                    f"MORPH-{cluster_id}",
                "forward_return_8":
                    base,
                "short_return_8":
                    -base,
                "long_mfe_8":
                    base * 1.5,
                "long_mae_8":
                    -base * 0.25,
                "short_mfe_8":
                    base * 0.25,
                "short_mae_8":
                    -base * 1.5,
                "forward_return_32":
                    base * 1.5,
                "short_return_32":
                    -base * 1.5,
                "long_mfe_32":
                    base * 2.0,
                "long_mae_32":
                    -base * 0.40,
                "short_mfe_32":
                    base * 0.40,
                "short_mae_32":
                    -base * 2.0,
            })

    return pd.DataFrame(rows)


def test_latest_windows_end_at_actual_latest_timestamp() -> None:
    assignments = _assignments(
        periods=41
    )

    morphology = build_timestamp_morphology(
        assignments
    )

    config = MorphologyTrajectoryConfig(
        sequence_lengths=(3, 4, 5),
        outcome_horizons=(8, 32),
        stride=4,
    )

    latest = build_latest_trajectory_windows(
        morphology,
        config=config,
    )

    assert latest[
        "window_end"
    ].nunique() == 1

    assert latest[
        "window_end"
    ].iloc[0] == morphology[
        "timestamp"
    ].max()


def test_walk_forward_boundaries_are_chronological() -> None:
    timestamps = pd.date_range(
        "2025-01-01",
        periods=200,
        freq="15min",
        tz="UTC",
    )

    folds = build_walk_forward_boundaries(
        pd.Series(timestamps),
        config=TrajectoryWalkForwardConfig(
            fold_count=4,
        ),
    )

    assert len(folds) == 4

    for fold in folds:
        assert (
            fold["train_start"]
            < fold["test_start"]
            <= fold["test_end"]
        )


def test_walk_forward_discovers_and_tests_candidates() -> None:
    trajectory_config = (
        MorphologyTrajectoryConfig(
            sequence_lengths=(3, 5),
            outcome_horizons=(8, 32),
            stride=1,
            risk_penalty=0.50,
        )
    )

    validation_config = (
        TrajectoryWalkForwardConfig(
            fold_count=4,
            minimum_training_observations=5,
            minimum_test_observations=2,
            initial_training_fraction=0.50,
            risk_penalty=0.50,
        )
    )

    folds = run_trajectory_walk_forward(
        _assignments(),
        trajectory_config=(
            trajectory_config
        ),
        validation_config=(
            validation_config
        ),
    )

    assert len(folds) == 16

    assert {
        "discovered_in_training",
        "test_eligible",
        "passed_test",
        "train_risk_adjusted_edge",
        "test_risk_adjusted_edge",
    }.issubset(
        folds.columns
    )


def test_walk_forward_summary_has_four_candidates() -> None:
    trajectory_config = (
        MorphologyTrajectoryConfig(
            sequence_lengths=(3, 5),
            outcome_horizons=(8, 32),
            stride=1,
        )
    )

    validation_config = (
        TrajectoryWalkForwardConfig(
            fold_count=3,
            minimum_training_observations=5,
            minimum_test_observations=2,
        )
    )

    folds = run_trajectory_walk_forward(
        _assignments(),
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

    assert len(summary) == 4

    assert {
        "fold_pass_rate",
        "weighted_test_mean_return",
        "promotion_candidate",
    }.issubset(
        summary.columns
    )
