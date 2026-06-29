"""Differential comparison utilities for topology graphs."""

from dataclasses import dataclass

from atlas.topology.graph import Edge, Node, TopologyGraph
from atlas.topology.overlay import shared_edges, shared_nodes, unique_edges, unique_nodes


@dataclass(frozen=True)
class GraphDifferential:
    """Structured comparison between two topology graphs."""

    shared_nodes: tuple[Node, ...]
    shared_edges: tuple[Edge, ...]
    unique_nodes_a: tuple[Node, ...]
    unique_nodes_b: tuple[Node, ...]
    unique_edges_a: tuple[Edge, ...]
    unique_edges_b: tuple[Edge, ...]
    node_weight_delta: dict[Node, int]
    edge_weight_delta: dict[Edge, int]
    node_overlap_ratio: float
    edge_overlap_ratio: float


def compare_graphs(
    graph_a: TopologyGraph,
    graph_b: TopologyGraph,
) -> GraphDifferential:
    """Compare two topology graphs.

    Delta convention:
    - positive value means graph_a is stronger
    - negative value means graph_b is stronger
    - zero means equal weight
    """
    common_nodes = shared_nodes(graph_a, graph_b)
    common_edges = shared_edges(graph_a, graph_b)

    only_nodes_a = unique_nodes(graph_a, graph_b)
    only_nodes_b = unique_nodes(graph_b, graph_a)

    only_edges_a = unique_edges(graph_a, graph_b)
    only_edges_b = unique_edges(graph_b, graph_a)

    all_nodes = tuple(dict.fromkeys(graph_a.nodes + graph_b.nodes))
    all_edges = tuple(dict.fromkeys(graph_a.edges + graph_b.edges))

    node_weight_delta = {
        node: graph_a.node_weights.get(node, 0) - graph_b.node_weights.get(node, 0)
        for node in all_nodes
    }

    edge_weight_delta = {
        edge: graph_a.edge_weights.get(edge, 0) - graph_b.edge_weights.get(edge, 0)
        for edge in all_edges
    }

    node_overlap_ratio = _overlap_ratio(len(common_nodes), len(all_nodes))
    edge_overlap_ratio = _overlap_ratio(len(common_edges), len(all_edges))

    return GraphDifferential(
        shared_nodes=common_nodes,
        shared_edges=common_edges,
        unique_nodes_a=only_nodes_a,
        unique_nodes_b=only_nodes_b,
        unique_edges_a=only_edges_a,
        unique_edges_b=only_edges_b,
        node_weight_delta=node_weight_delta,
        edge_weight_delta=edge_weight_delta,
        node_overlap_ratio=node_overlap_ratio,
        edge_overlap_ratio=edge_overlap_ratio,
    )


def _overlap_ratio(shared_count: int, total_count: int) -> float:
    """Return shared / total, guarding against empty graphs."""
    if total_count == 0:
        return 0.0

    return shared_count / total_count