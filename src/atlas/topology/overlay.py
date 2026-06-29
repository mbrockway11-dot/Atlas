"""Overlay utilities for combining topology graphs."""

from collections import defaultdict

from atlas.topology.graph import Edge, Node, TopologyGraph


def overlay_graphs(graphs: list[TopologyGraph]) -> TopologyGraph:
    """Combine multiple topology graphs into one weighted overlay.

    Rules:
    - Shared nodes have their weights summed.
    - Shared edges have their weights summed.
    - Unique nodes and edges are preserved.
    - Node and edge order follows first appearance across graphs.
    """
    node_weights: dict[Node, int] = defaultdict(int)
    edge_weights: dict[Edge, int] = defaultdict(int)

    ordered_nodes: list[Node] = []
    ordered_edges: list[Edge] = []

    seen_nodes: set[Node] = set()
    seen_edges: set[Edge] = set()

    for graph in graphs:
        for node in graph.nodes:
            if node not in seen_nodes:
                ordered_nodes.append(node)
                seen_nodes.add(node)

            node_weights[node] += graph.node_weights.get(node, 0)

        for edge in graph.edges:
            if edge not in seen_edges:
                ordered_edges.append(edge)
                seen_edges.add(edge)

            edge_weights[edge] += graph.edge_weights.get(edge, 0)

    return TopologyGraph(
        nodes=tuple(ordered_nodes),
        edges=tuple(ordered_edges),
        node_weights=dict(node_weights),
        edge_weights=dict(edge_weights),
    )


def overlay_pair(
    graph_a: TopologyGraph,
    graph_b: TopologyGraph,
) -> TopologyGraph:
    """Overlay exactly two graphs."""
    return overlay_graphs([graph_a, graph_b])


def shared_nodes(
    graph_a: TopologyGraph,
    graph_b: TopologyGraph,
) -> tuple[Node, ...]:
    """Return nodes present in both graphs."""
    graph_b_nodes = set(graph_b.nodes)

    return tuple(
        node for node in graph_a.nodes
        if node in graph_b_nodes
    )


def shared_edges(
    graph_a: TopologyGraph,
    graph_b: TopologyGraph,
) -> tuple[Edge, ...]:
    """Return edges present in both graphs."""
    graph_b_edges = set(graph_b.edges)

    return tuple(
        edge for edge in graph_a.edges
        if edge in graph_b_edges
    )


def unique_nodes(
    graph_a: TopologyGraph,
    graph_b: TopologyGraph,
) -> tuple[Node, ...]:
    """Return nodes present in graph_a but not graph_b."""
    graph_b_nodes = set(graph_b.nodes)

    return tuple(
        node for node in graph_a.nodes
        if node not in graph_b_nodes
    )


def unique_edges(
    graph_a: TopologyGraph,
    graph_b: TopologyGraph,
) -> tuple[Edge, ...]:
    """Return edges present in graph_a but not graph_b."""
    graph_b_edges = set(graph_b.edges)

    return tuple(
        edge for edge in graph_a.edges
        if edge not in graph_b_edges
    )