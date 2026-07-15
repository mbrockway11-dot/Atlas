from __future__ import annotations

import numpy as np
import pandas as pd

from atlas.investment.morphology_intelligence.graph import (
    MorphologyGraphConfig,
    build_adjacency_matrix,
    build_edge_outcome_map,
    build_graph_edges,
    build_graph_forecasts,
    build_graph_nodes,
    calculate_pagerank,
    transition_entropy,
)


def _profiles() -> pd.DataFrame:
    rows = []

    for cluster_id in range(3):
        for asset in (
            "BTC",
            "ETH",
            "SOL",
        ):
            rows.append({
                "morphology_cluster_id":
                    cluster_id,
                "morphology_cluster":
                    f"MORPH-{cluster_id}",
                "asset":
                    asset,
                "observation_count":
                    100 + cluster_id,
                "dominant_rank_state":
                    "BTC>ETH>SOL",
                "dominant_transition":
                    "BTC>ETH>SOL->BTC>ETH>SOL",
                "mean_entropy":
                    0.5 + cluster_id * 0.1,
                "long_mean_return_16":
                    0.01 * cluster_id,
                "long_win_rate_16":
                    0.50 + cluster_id * 0.02,
                "short_mean_return_16":
                    -0.005 * cluster_id,
                "short_win_rate_16":
                    0.50 - cluster_id * 0.01,
            })

    return pd.DataFrame(rows)


def _edges() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "morphology_cluster_id": 0,
            "morphology_cluster": "MORPH-0",
            "next_cluster_id": 0,
            "next_cluster": "MORPH-0",
            "transition_count": 80,
            "transition_probability": 0.8,
        },
        {
            "morphology_cluster_id": 0,
            "morphology_cluster": "MORPH-0",
            "next_cluster_id": 1,
            "next_cluster": "MORPH-1",
            "transition_count": 20,
            "transition_probability": 0.2,
        },
        {
            "morphology_cluster_id": 1,
            "morphology_cluster": "MORPH-1",
            "next_cluster_id": 2,
            "next_cluster": "MORPH-2",
            "transition_count": 100,
            "transition_probability": 1.0,
        },
        {
            "morphology_cluster_id": 2,
            "morphology_cluster": "MORPH-2",
            "next_cluster_id": 2,
            "next_cluster": "MORPH-2",
            "transition_count": 100,
            "transition_probability": 1.0,
        },
    ])


def _assignments() -> pd.DataFrame:
    timestamps = pd.date_range(
        "2026-01-01",
        periods=5,
        freq="15min",
        tz="UTC",
    )

    rows = []

    clusters = [
        0,
        0,
        1,
        2,
        2,
    ]

    for asset in (
        "BTC",
        "ETH",
        "SOL",
    ):
        for index, timestamp in enumerate(
            timestamps
        ):
            cluster_id = clusters[index]

            rows.append({
                "timestamp": timestamp,
                "asset": asset,
                "morphology_cluster_id":
                    cluster_id,
                "morphology_cluster":
                    f"MORPH-{cluster_id}",
                "forward_return_16":
                    0.01 * (
                        cluster_id + 1
                    ),
                "short_return_16":
                    -0.005 * (
                        cluster_id + 1
                    ),
            })

    return pd.DataFrame(rows)


def test_transition_entropy_is_normalized() -> None:
    assert transition_entropy(
        [1.0]
    ) == 0.0

    assert np.isclose(
        transition_entropy(
            [0.5, 0.5]
        ),
        1.0,
    )


def test_adjacency_rows_sum_to_one() -> None:
    matrix, node_ids = (
        build_adjacency_matrix(
            _edges(),
            node_ids=(0, 1, 2),
        )
    )

    assert node_ids == (
        0,
        1,
        2,
    )

    assert np.allclose(
        matrix.sum(axis=1),
        1.0,
    )


def test_pagerank_sums_to_one() -> None:
    matrix, _ = build_adjacency_matrix(
        _edges(),
        node_ids=(0, 1, 2),
    )

    ranks, _, converged = (
        calculate_pagerank(
            matrix,
            damping=0.85,
            tolerance=1e-12,
            maximum_iterations=1000,
        )
    )

    assert converged
    assert np.isclose(
        ranks.sum(),
        1.0,
    )


def test_graph_nodes_include_structural_metrics() -> None:
    nodes, metadata = build_graph_nodes(
        _profiles(),
        _edges(),
        config=MorphologyGraphConfig(),
    )

    assert len(nodes) == 3
    assert metadata[
        "pagerank_converged"
    ]

    assert {
        "pagerank",
        "transition_entropy",
        "self_transition_probability",
        "dominant_next_cluster",
    }.issubset(
        nodes.columns
    )


def test_graph_edges_include_strength() -> None:
    edges = build_graph_edges(
        _edges()
    )

    assert {
        "edge_strength",
        "edge_surprise",
        "is_self_transition",
    }.issubset(
        edges.columns
    )


def test_graph_forecasts_are_probabilities() -> None:
    forecasts, paths = (
        build_graph_forecasts(
            _edges(),
            node_ids=(0, 1, 2),
            config=MorphologyGraphConfig(
                forecast_depth=3,
                top_paths_per_source=5,
            ),
        )
    )

    grouped = (
        forecasts.groupby(
            [
                "source_cluster_id",
                "forecast_step",
            ]
        )[
            "forecast_probability"
        ]
        .sum()
    )

    assert np.allclose(
        grouped.to_numpy(),
        1.0,
    )

    assert not paths.empty


def test_edge_outcomes_are_asset_specific() -> None:
    outcomes = build_edge_outcome_map(
        _assignments(),
        horizon=16,
    )

    assert set(
        outcomes["asset"]
    ) == {
        "BTC",
        "ETH",
        "SOL",
    }

    assert {
        "preferred_direction",
        "preferred_mean_return",
    }.issubset(
        outcomes.columns
    )
