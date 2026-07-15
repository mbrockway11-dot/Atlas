from __future__ import annotations

import numpy as np
import pandas as pd

from atlas.investment.morphology_intelligence.trajectory import (
    MorphologyTrajectoryConfig,
    attach_asset_outcomes,
    build_timestamp_morphology,
    build_trajectory_transition_map,
    extract_trajectory_windows,
    profile_trajectory_outcomes,
    recognize_latest_trajectories,
    run_morphology_trajectory_engine,
    trajectory_shape_metrics,
)


def _assignments(
    periods: int = 80,
) -> pd.DataFrame:
    timestamps = pd.date_range(
        "2025-01-01",
        periods=periods,
        freq="15min",
        tz="UTC",
    )

    pattern = [
        0,
        0,
        1,
        1,
        2,
        2,
        1,
        1,
    ]

    rows = []

    for timestamp_index, timestamp in enumerate(
        timestamps
    ):
        cluster_id = pattern[
            timestamp_index
            % len(pattern)
        ]

        for asset_index, asset in enumerate(
            ("BTC", "ETH", "SOL")
        ):
            edge = (
                0.001
                * (
                    cluster_id + 1
                )
                * (
                    asset_index + 1
                )
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
                "forward_return_4":
                    edge,
                "short_return_4":
                    -edge,
                "long_mfe_4":
                    edge * 1.5,
                "long_mae_4":
                    -edge * 0.5,
                "short_mfe_4":
                    edge * 0.5,
                "short_mae_4":
                    -edge * 1.5,
                "forward_return_8":
                    edge * 2.0,
                "short_return_8":
                    -edge * 2.0,
                "long_mfe_8":
                    edge * 2.5,
                "long_mae_8":
                    -edge * 0.75,
                "short_mfe_8":
                    edge * 0.75,
                "short_mae_8":
                    -edge * 2.5,
            })

    return pd.DataFrame(rows)


def _config() -> MorphologyTrajectoryConfig:
    return MorphologyTrajectoryConfig(
        sequence_lengths=(3, 4),
        outcome_horizons=(4, 8),
        minimum_observations=2,
        confidence_target=5,
        stride=1,
        risk_penalty=0.25,
    )


def test_timestamp_morphology_is_unique() -> None:
    assignments = _assignments()

    morphology = build_timestamp_morphology(
        assignments
    )

    assert len(morphology) == (
        assignments[
            "timestamp"
        ].nunique()
    )

    assert morphology[
        "timestamp"
    ].is_unique


def test_trajectory_shapes_are_classified() -> None:
    persistent = trajectory_shape_metrics(
        [1, 1, 1, 1]
    )

    oscillating = trajectory_shape_metrics(
        [1, 2, 1, 2]
    )

    progressive = trajectory_shape_metrics(
        [1, 2, 3, 4]
    )

    assert (
        persistent[
            "trajectory_shape"
        ]
        == "PERSISTENT"
    )

    assert (
        oscillating[
            "trajectory_shape"
        ]
        == "OSCILLATING"
    )

    assert (
        progressive[
            "trajectory_shape"
        ]
        == "PROGRESSIVE"
    )


def test_windows_have_expected_lengths() -> None:
    morphology = build_timestamp_morphology(
        _assignments(periods=20)
    )

    windows = extract_trajectory_windows(
        morphology,
        config=_config(),
    )

    assert set(
        windows[
            "sequence_length"
        ]
    ) == {
        3,
        4,
    }

    assert windows[
        "trajectory_id"
    ].notna().all()


def test_asset_outcomes_are_attached() -> None:
    assignments = _assignments(
        periods=20
    )

    morphology = build_timestamp_morphology(
        assignments
    )

    windows = extract_trajectory_windows(
        morphology,
        config=_config(),
    )

    observations = attach_asset_outcomes(
        windows,
        assignments,
        config=_config(),
    )

    assert set(
        observations["asset"]
    ) == {
        "BTC",
        "ETH",
        "SOL",
    }

    assert len(observations) == (
        len(windows) * 3
    )


def test_profiles_are_asset_specific() -> None:
    result = (
        run_morphology_trajectory_engine(
            _assignments(),
            config=_config(),
        )
    )

    profiles = result["profiles"]

    assert set(
        profiles["asset"]
    ) == {
        "BTC",
        "ETH",
        "SOL",
    }

    assert {
        "recommended_action",
        "recommended_direction",
        "optimal_horizon_bars",
        "trajectory_score",
    }.issubset(
        profiles.columns
    )


def test_profitable_long_trajectory_is_detected() -> None:
    result = (
        run_morphology_trajectory_engine(
            _assignments(),
            config=_config(),
        )
    )

    profiles = result["profiles"]

    entered = profiles[
        profiles[
            "recommended_action"
        ].eq("ENTER")
    ]

    assert not entered.empty

    assert entered[
        "recommended_direction"
    ].eq("LONG").all()


def test_trajectory_transition_probabilities_sum_to_one() -> None:
    result = (
        run_morphology_trajectory_engine(
            _assignments(),
            config=_config(),
        )
    )

    transitions = result[
        "transitions"
    ]

    sums = (
        transitions.groupby(
            [
                "sequence_length",
                "trajectory_id",
            ]
        )[
            "transition_probability"
        ]
        .sum()
    )

    assert np.allclose(
        sums.to_numpy(),
        1.0,
    )


def test_latest_trajectory_is_recognized_per_length_and_asset() -> None:
    result = (
        run_morphology_trajectory_engine(
            _assignments(),
            config=_config(),
        )
    )

    latest = result["latest"]

    assert set(
        latest[
            "sequence_length"
        ]
    ) == {
        3,
        4,
    }

    assert set(
        latest["asset"]
    ) == {
        "BTC",
        "ETH",
        "SOL",
    }

    assert len(latest) == 6
