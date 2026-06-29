"""Structural similarity metrics for topology graphs."""

from __future__ import annotations

from dataclasses import dataclass

from atlas.topology.differential import compare_graphs
from atlas.topology.graph import Edge, Node, TopologyGraph


@dataclass(frozen=True)
class StructuralSimilarity:
    """Explainable similarity result between two topology graphs."""

    node_overlap: float
    edge_overlap: float
    node_weight_similarity: float
    edge_weight_similarity: float
    structural_similarity: float
    strongest_shared_nodes: tuple[Node, ...]
    strongest_shared_edges: tuple[Edge, ...]
    strongest_node_deltas: dict[Node, int]
    strongest_edge_deltas: dict[Edge, int]


def compare_structural_similarity(
    graph_a: TopologyGraph,
    graph_b: TopologyGraph,
    *,
    top_n: int = 5,
) -> StructuralSimilarity:
    """Compare two topology graphs using deterministic structural metrics."""

    differential = compare_graphs(graph_a, graph_b)

    node_weight_similarity = _weight_similarity(
        graph_a.node_weights,
        graph_b.node_weights,
    )

    edge_weight_similarity = _weight_similarity(
        graph_a.edge_weights,
        graph_b.edge_weights,
    )

    structural_similarity = _mean(
        (
            differential.node_overlap_ratio,
            differential.edge_overlap_ratio,
            node_weight_similarity,
            edge_weight_similarity,
        )
    )

    strongest_shared_nodes = _strongest_shared_items(
        differential.shared_nodes,
        graph_a.node_weights,
        graph_b.node_weights,
        top_n=top_n,
    )

    strongest_shared_edges = _strongest_shared_items(
        differential.shared_edges,
        graph_a.edge_weights,
        graph_b.edge_weights,
        top_n=top_n,
    )

    strongest_node_deltas = _strongest_deltas(
        differential.node_weight_delta,
        top_n=top_n,
    )

    strongest_edge_deltas = _strongest_deltas(
        differential.edge_weight_delta,
        top_n=top_n,
    )

    return StructuralSimilarity(
        node_overlap=differential.node_overlap_ratio,
        edge_overlap=differential.edge_overlap_ratio,
        node_weight_similarity=node_weight_similarity,
        edge_weight_similarity=edge_weight_similarity,
        structural_similarity=structural_similarity,
        strongest_shared_nodes=strongest_shared_nodes,
        strongest_shared_edges=strongest_shared_edges,
        strongest_node_deltas=strongest_node_deltas,
        strongest_edge_deltas=strongest_edge_deltas,
    )


def _weight_similarity(
    weights_a: dict[object, int],
    weights_b: dict[object, int],
) -> float:
    """Return normalized similarity between two weight maps."""

    keys = set(weights_a) | set(weights_b)

    if not keys:
        return 0.0

    total_delta = sum(
        abs(weights_a.get(key, 0) - weights_b.get(key, 0))
        for key in keys
    )

    total_mass = sum(
        max(weights_a.get(key, 0), weights_b.get(key, 0))
        for key in keys
    )

    if total_mass == 0:
        return 0.0

    return 1.0 - (total_delta / total_mass)


def _strongest_shared_items(
    shared_items: tuple[object, ...],
    weights_a: dict[object, int],
    weights_b: dict[object, int],
    *,
    top_n: int,
) -> tuple:
    """Return shared items ranked by combined weight."""

    return tuple(
        item
        for item, _ in sorted(
            (
                (
                    item,
                    weights_a.get(item, 0) + weights_b.get(item, 0),
                )
                for item in shared_items
            ),
            key=lambda pair: pair[1],
            reverse=True,
        )[:top_n]
    )


def _strongest_deltas(
    deltas: dict[object, int],
    *,
    top_n: int,
) -> dict:
    """Return largest absolute weight deltas."""

    return dict(
        sorted(
            deltas.items(),
            key=lambda pair: abs(pair[1]),
            reverse=True,
        )[:top_n]
    )


def _mean(values: tuple[float, ...]) -> float:
    """Return arithmetic mean."""

    if not values:
        return 0.0

    return sum(values) / len(values)