"""Population topology service utilities."""

from __future__ import annotations

from typing import Any

import pandas as pd

from atlas.research.population_topology import (
    build_population_topology_graph,
    population_topology_report_to_json,
    topology_edges_dataframe,
    topology_nodes_dataframe,
)
from atlas.services.validation_service import get_profile_feature_matrix


def get_topology_profile_features() -> pd.DataFrame:
    """Return profile-level features for topology analysis."""
    return get_profile_feature_matrix()


def get_population_topology_graph(
    profile_features: pd.DataFrame | None = None,
    *,
    threshold: float = 0.75,
    top_k: int = 5,
    metric: str = "cosine",
) -> dict[str, Any]:
    """Return population topology graph."""
    features = profile_features if profile_features is not None else get_topology_profile_features()

    return build_population_topology_graph(
        features,
        threshold=threshold,
        top_k=top_k,
        metric=metric,
    )


def get_topology_node(
    profile_name: str,
    profile_features: pd.DataFrame | None = None,
    *,
    threshold: float = 0.75,
    top_k: int = 5,
    metric: str = "cosine",
) -> dict[str, Any] | None:
    """Return topology node for selected profile name."""
    graph = get_population_topology_graph(
        profile_features,
        threshold=threshold,
        top_k=top_k,
        metric=metric,
    )
    return graph.get("nodes", {}).get(profile_name)


def get_topology_nodes_dataframe(graph: dict[str, Any]) -> pd.DataFrame:
    """Return topology nodes dataframe."""
    return topology_nodes_dataframe(graph)


def get_topology_edges_dataframe(graph: dict[str, Any]) -> pd.DataFrame:
    """Return topology edges dataframe."""
    return topology_edges_dataframe(graph)


def topology_json(graph: dict[str, Any]) -> str:
    """Serialize topology report."""
    return population_topology_report_to_json(graph)