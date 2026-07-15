from __future__ import annotations

import numpy as np
import pandas as pd

from atlas.investment.morphology_intelligence.evolution import (
    MorphologyEvolutionConfig,
    build_cluster_centroids,
    build_motion_features,
    build_timestamp_geometry,
    calculate_attractor_observations,
    run_morphology_evolution,
    select_attractor_clusters,
    select_nearest_attractor,
)


def _assignments(
    periods: int = 100,
) -> pd.DataFrame:
    timestamps = pd.date_range(
        "2025-01-01",
        periods=periods,
        freq="15min",
        tz="UTC",
    )

    rows = []

    for index, timestamp in enumerate(
        timestamps
    ):
        cluster_id = (
            0
            if index < periods // 2
            else 1
        )

        for asset in (
            "BTC",
            "ETH",
            "SOL",
        ):
            rows.append({
                "timestamp": timestamp,
                "asset": asset,
                "morphology_cluster_id":
                    cluster_id,
                "morphology_cluster":
                    f"MORPH-{cluster_id}",
                "morphology_pc_1":
                    float(index) / 10.0,
                "morphology_pc_2":
                    float(index ** 2) / 1000.0,
                "morphology_pc_3":
                    float(cluster_id),
            })

    return pd.DataFrame(rows)


def _profiles() -> pd.DataFrame:
    rows = []

    for cluster_id in (
        0,
        1,
    ):
        for asset_index, asset in enumerate(
            (
                "BTC",
                "ETH",
                "SOL",
            )
        ):
            rows.append({
                "morphology_cluster_id":
                    cluster_id,
                "morphology_cluster":
                    f"MORPH-{cluster_id}",
                "asset":
                    asset,
                "observation_count":
                    1000,
                "long_mean_return_16":
                    0.001
                    * (
                        cluster_id + 1
                    )
                    * (
                        asset_index + 1
                    ),
                "long_win_rate_16":
                    0.55
                    + cluster_id * 0.05,
            })

    return pd.DataFrame(rows)


def _config() -> MorphologyEvolutionConfig:
    return MorphologyEvolutionConfig(
        derivative_lag=1,
        smoothing_window=3,
        attractor_horizon=16,
        minimum_attractor_observations=10,
        attractors_per_asset=1,
        stability_window=4,
    )


def test_timestamp_geometry_is_unique() -> None:
    geometry = build_timestamp_geometry(
        _assignments()
    )

    assert geometry[
        "timestamp"
    ].is_unique

    assert len(geometry) == 100


def test_motion_features_include_dynamics() -> None:
    geometry = build_timestamp_geometry(
        _assignments()
    )

    motion = build_motion_features(
        geometry,
        config=_config(),
    )

    required = {
        "morphology_speed",
        "morphology_acceleration_magnitude",
        "morphology_curvature",
        "morphology_directional_stability",
        "morphology_motion_state",
    }

    assert required.issubset(
        motion.columns
    )

    assert motion[
        "morphology_speed"
    ].ge(0.0).all()


def test_centroids_exist_per_cluster() -> None:
    geometry = build_timestamp_geometry(
        _assignments()
    )

    centroids = build_cluster_centroids(
        geometry
    )

    assert set(
        centroids[
            "morphology_cluster_id"
        ]
    ) == {
        0,
        1,
    }


def test_attractors_are_selected_per_asset() -> None:
    attractors = select_attractor_clusters(
        _profiles(),
        config=_config(),
    )

    assert set(
        attractors["asset"]
    ) == {
        "BTC",
        "ETH",
        "SOL",
    }

    assert (
        attractors.groupby(
            "asset"
        ).size() == 1
    ).all()


def test_attractor_distance_and_eta_are_created() -> None:
    result = run_morphology_evolution(
        assignments=_assignments(),
        profiles=_profiles(),
        config=_config(),
    )

    observations = result[
        "attractor_observations"
    ]

    assert {
        "distance_to_attractor",
        "attractor_closing_velocity",
        "estimated_bars_to_attractor",
        "attractor_alignment_score",
    }.issubset(
        observations.columns
    )

    assert observations[
        "distance_to_attractor"
    ].ge(0.0).all()


def test_nearest_attractor_has_one_row_per_asset_timestamp() -> None:
    result = run_morphology_evolution(
        assignments=_assignments(),
        profiles=_profiles(),
        config=_config(),
    )

    nearest = result[
        "nearest_attractors"
    ]

    counts = nearest.groupby(
        [
            "timestamp",
            "asset",
        ]
    ).size()

    assert counts.eq(1).all()


def test_latest_timestamp_contains_all_assets() -> None:
    result = run_morphology_evolution(
        assignments=_assignments(),
        profiles=_profiles(),
        config=_config(),
    )

    nearest = result[
        "nearest_attractors"
    ]

    latest = nearest[
        nearest["timestamp"].eq(
            nearest["timestamp"].max()
        )
    ]

    assert set(
        latest["asset"]
    ) == {
        "BTC",
        "ETH",
        "SOL",
    }


def test_motion_is_point_in_time_only() -> None:
    assignments = _assignments()
    geometry = build_timestamp_geometry(
        assignments
    )

    original = build_motion_features(
        geometry,
        config=_config(),
    )

    modified = assignments.copy()

    modified[
        "future_fake_label"
    ] = np.arange(
        len(modified)
    )

    modified_geometry = (
        build_timestamp_geometry(
            modified
        )
    )

    repeated = build_motion_features(
        modified_geometry,
        config=_config(),
    )

    assert np.allclose(
        original[
            "morphology_speed"
        ],
        repeated[
            "morphology_speed"
        ],
    )
