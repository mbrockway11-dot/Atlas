from __future__ import annotations

import numpy as np
import pandas as pd

from atlas.investment.morphology_intelligence.clustering import (
    MorphologyClusteringConfig,
    assign_clusters,
    build_cluster_assignments,
    build_cluster_profiles,
    build_cluster_transition_matrix,
    fit_kmeans,
    fit_pca,
    fit_standardizer,
    run_morphology_clustering,
    transform_pca,
    transform_standardized,
)


def _observations(
    periods: int = 300,
) -> pd.DataFrame:
    rows = []

    timestamps = pd.date_range(
        "2025-01-01",
        periods=periods,
        freq="15min",
        tz="UTC",
    )

    for index, timestamp in enumerate(
        timestamps
    ):
        regime = index % 3

        for asset_index, asset in enumerate(
            ("BTC", "ETH", "SOL")
        ):
            base = float(
                regime * 3
                + asset_index * 0.1
            )

            rows.append({
                "timestamp": timestamp,
                "asset": asset,
                "rank_state": (
                    "BTC>ETH>SOL"
                    if regime == 0
                    else (
                        "ETH>SOL>BTC"
                        if regime == 1
                        else "SOL>BTC>ETH"
                    )
                ),
                "transition": (
                    "STATE_A->STATE_A"
                    if regime == 0
                    else (
                        "STATE_B->STATE_B"
                        if regime == 1
                        else "STATE_C->STATE_C"
                    )
                ),
                "entropy":
                    0.1 + base,
                "transition_velocity":
                    0.2 + base,
                "multi_timeframe_agreement":
                    0.3 + base,
                "concentration":
                    0.4 + base,
                "dispersion":
                    0.5 + base,
                "persistence_bars":
                    1.0 + base,
                "sol_fulcrum_score":
                    -0.2 + base,
                "forward_return_1":
                    0.001 * (
                        regime - 1
                    ),
                "short_return_1":
                    -0.001 * (
                        regime - 1
                    ),
                "forward_return_2":
                    0.002 * (
                        regime - 1
                    ),
                "short_return_2":
                    -0.002 * (
                        regime - 1
                    ),
                "forward_return_4":
                    0.004 * (
                        regime - 1
                    ),
                "short_return_4":
                    -0.004 * (
                        regime - 1
                    ),
                "forward_return_8":
                    0.008 * (
                        regime - 1
                    ),
                "short_return_8":
                    -0.008 * (
                        regime - 1
                    ),
                "forward_return_16":
                    0.016 * (
                        regime - 1
                    ),
                "short_return_16":
                    -0.016 * (
                        regime - 1
                    ),
                "forward_return_32":
                    0.032 * (
                        regime - 1
                    ),
                "short_return_32":
                    -0.032 * (
                        regime - 1
                    ),
                "forward_return_96":
                    0.096 * (
                        regime - 1
                    ),
                "short_return_96":
                    -0.096 * (
                        regime - 1
                    ),
            })

    return pd.DataFrame(rows)


def _config() -> MorphologyClusteringConfig:
    return MorphologyClusteringConfig(
        cluster_counts=(3, 4),
        selected_cluster_count=3,
        pca_components=3,
        fit_sample_size=500,
        diagnostic_sample_size=500,
        maximum_iterations=50,
        random_seed=11,
    )


def test_standardization_is_centered() -> None:
    observations = _observations()

    model = fit_standardizer(
        observations,
        columns=_config().feature_columns,
    )

    transformed = transform_standardized(
        observations,
        model,
    )

    assert np.allclose(
        transformed.mean(axis=0),
        0.0,
        atol=1e-10,
    )


def test_pca_reduces_dimension() -> None:
    observations = _observations()
    config = _config()

    standardizer = fit_standardizer(
        observations,
        columns=config.feature_columns,
    )

    standardized = transform_standardized(
        observations,
        standardizer,
    )

    model = fit_pca(
        standardized,
        feature_columns=config.feature_columns,
        component_count=3,
    )

    projected = transform_pca(
        standardized,
        model,
    )

    assert projected.shape == (
        len(observations),
        3,
    )

    assert (
        sum(
            model.explained_variance_ratio
        )
        <= 1.0 + 1e-12
    )


def test_kmeans_is_deterministic() -> None:
    matrix = np.asarray([
        [0.0, 0.0],
        [0.1, 0.1],
        [10.0, 10.0],
        [10.1, 10.1],
    ])

    first = fit_kmeans(
        matrix,
        cluster_count=2,
        maximum_iterations=20,
        convergence_tolerance=1e-9,
        random_seed=7,
    )

    second = fit_kmeans(
        matrix,
        cluster_count=2,
        maximum_iterations=20,
        convergence_tolerance=1e-9,
        random_seed=7,
    )

    assert first.centroids == second.centroids
    assert first.inertia == second.inertia


def test_cluster_assignment_is_complete() -> None:
    observations = _observations()
    result = run_morphology_clustering(
        observations,
        config=_config(),
    )

    assignments = result[
        "assignments"
    ]

    assert len(assignments) == len(
        observations
    )

    assert assignments[
        "morphology_cluster"
    ].notna().all()

    assert assignments[
        "morphology_cluster_distance"
    ].ge(0.0).all()


def test_cluster_profiles_use_outcomes_after_assignment() -> None:
    observations = _observations()
    result = run_morphology_clustering(
        observations,
        config=_config(),
    )

    profiles = result[
        "profiles"
    ]

    assert not profiles.empty

    assert "long_mean_return_16" in (
        profiles.columns
    )

    assert "short_win_rate_16" in (
        profiles.columns
    )


def test_cluster_transitions_sum_to_one() -> None:
    observations = _observations()
    result = run_morphology_clustering(
        observations,
        config=_config(),
    )

    transitions = result[
        "transitions"
    ]

    sums = (
        transitions.groupby(
            "morphology_cluster_id"
        )[
            "transition_probability"
        ]
        .sum()
    )

    assert np.allclose(
        sums.to_numpy(),
        1.0,
    )


def test_future_outcomes_are_not_clustering_features() -> None:
    config = _config()

    assert not any(
        column.startswith(
            "forward_return"
        )
        for column in config.feature_columns
    )

    assert not any(
        "mfe" in column
        or "mae" in column
        for column in config.feature_columns
    )


def test_clustering_fits_unique_timestamps_and_profiles_assets_separately() -> None:
    observations = _observations()
    config = _config()

    result = run_morphology_clustering(
        observations,
        config=config,
    )

    assert len(result["fit_frame"]) <= (
        observations["timestamp"].nunique()
    )

    profiles = result["profiles"]

    assert "asset" in profiles.columns

    assert set(
        profiles["asset"]
    ) == {
        "BTC",
        "ETH",
        "SOL",
    }

    counts = (
        result["assignments"]
        .groupby("timestamp")[
            "morphology_cluster_id"
        ]
        .nunique()
    )

    assert counts.eq(1).all()


def test_clustering_fits_unique_timestamps_and_profiles_assets_separately() -> None:
    observations = _observations()
    config = _config()

    result = run_morphology_clustering(
        observations,
        config=config,
    )

    assert len(result["fit_frame"]) <= (
        observations["timestamp"].nunique()
    )

    profiles = result["profiles"]

    assert "asset" in profiles.columns

    assert set(
        profiles["asset"]
    ) == {
        "BTC",
        "ETH",
        "SOL",
    }

    counts = (
        result["assignments"]
        .groupby("timestamp")[
            "morphology_cluster_id"
        ]
        .nunique()
    )

    assert counts.eq(1).all()
