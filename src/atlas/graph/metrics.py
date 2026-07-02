"""Graph metrics for unified AtlasGraph objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas.graph.semantic import AtlasGraph


GRAPH_METRICS_VERSION = "0.1"


@dataclass(frozen=True)
class GraphMetrics:
    """Computed graph metrics for an AtlasGraph."""

    node_count: int
    edge_count: int
    density: float
    average_degree: float
    max_degree: int
    isolated_nodes: tuple[str, ...]
    hub_nodes: tuple[str, ...]
    degree_by_node: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe graph metrics payload."""
        return {
            "version": GRAPH_METRICS_VERSION,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "density": self.density,
            "average_degree": self.average_degree,
            "max_degree": self.max_degree,
            "isolated_nodes": list(self.isolated_nodes),
            "hub_nodes": list(self.hub_nodes),
            "degree_by_node": self.degree_by_node,
        }


def compute_graph_metrics(graph: AtlasGraph) -> GraphMetrics:
    """Compute deterministic structural metrics for an AtlasGraph."""
    node_ids = [
        node.id
        for node in graph.nodes
    ]

    degree_by_node = {
        node_id: 0
        for node_id in node_ids
    }

    for edge in graph.edges:
        if edge.source in degree_by_node:
            degree_by_node[edge.source] += 1

        if edge.target in degree_by_node:
            degree_by_node[edge.target] += 1

    node_count = graph.node_count
    edge_count = graph.edge_count
    max_degree = max(degree_by_node.values(), default=0)

    isolated_nodes = tuple(
        node_id
        for node_id, degree in degree_by_node.items()
        if degree == 0
    )

    hub_nodes = tuple(
        node_id
        for node_id, degree in degree_by_node.items()
        if degree == max_degree and max_degree > 0
    )

    return GraphMetrics(
        node_count=node_count,
        edge_count=edge_count,
        density=_density(node_count, edge_count),
        average_degree=_average_degree(degree_by_node),
        max_degree=max_degree,
        isolated_nodes=isolated_nodes,
        hub_nodes=hub_nodes,
        degree_by_node=degree_by_node,
    )


def _density(
    node_count: int,
    edge_count: int,
) -> float:
    """Return directed graph density."""
    if node_count <= 1:
        return 0.0

    possible_edges = node_count * (node_count - 1)

    if possible_edges == 0:
        return 0.0

    return edge_count / possible_edges


def _average_degree(
    degree_by_node: dict[str, int],
) -> float:
    """Return average node degree."""
    if not degree_by_node:
        return 0.0

    return sum(degree_by_node.values()) / len(degree_by_node)
