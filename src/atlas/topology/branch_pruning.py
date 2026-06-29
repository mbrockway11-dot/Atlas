"""Branch pruning utilities for topology graphs."""

from atlas.topology.graph import Edge, Node, TopologyGraph


def prune_graph(
    graph: TopologyGraph,
    min_node_weight: int = 1,
    min_edge_weight: int = 1,
) -> TopologyGraph:
    """Return a pruned graph using minimum node and edge weights.

    Rules:
    - Nodes below min_node_weight are removed.
    - Edges below min_edge_weight are removed.
    - Edges connected to removed nodes are removed.
    - Final graph contains only active connected path structure.
    """
    kept_nodes = tuple(
        node
        for node in graph.nodes
        if graph.node_weights.get(node, 0) >= min_node_weight
    )

    kept_node_set = set(kept_nodes)

    kept_edges = tuple(
        edge
        for edge in graph.edges
        if graph.edge_weights.get(edge, 0) >= min_edge_weight
        and edge[0] in kept_node_set
        and edge[1] in kept_node_set
    )

    active_nodes = set()
    for source, target in kept_edges:
        active_nodes.add(source)
        active_nodes.add(target)

    final_nodes = tuple(
        node
        for node in kept_nodes
        if node in active_nodes or graph.node_weights.get(node, 0) >= min_node_weight
    )

    final_node_set = set(final_nodes)

    final_edges = tuple(
        edge
        for edge in kept_edges
        if edge[0] in final_node_set and edge[1] in final_node_set
    )

    final_node_weights: dict[Node, int] = {
        node: graph.node_weights[node]
        for node in final_nodes
    }

    final_edge_weights: dict[Edge, int] = {
        edge: graph.edge_weights[edge]
        for edge in final_edges
    }

    return TopologyGraph(
        nodes=final_nodes,
        edges=final_edges,
        node_weights=final_node_weights,
        edge_weights=final_edge_weights,
    )


def prune_isolated_nodes(graph: TopologyGraph) -> TopologyGraph:
    """Remove nodes with no incoming or outgoing edges."""
    connected_nodes = set()

    for source, target in graph.edges:
        connected_nodes.add(source)
        connected_nodes.add(target)

    kept_nodes = tuple(
        node for node in graph.nodes
        if node in connected_nodes
    )

    kept_node_weights: dict[Node, int] = {
        node: graph.node_weights[node]
        for node in kept_nodes
    }

    kept_edges = tuple(
        edge for edge in graph.edges
        if edge[0] in connected_nodes and edge[1] in connected_nodes
    )

    kept_edge_weights: dict[Edge, int] = {
        edge: graph.edge_weights[edge]
        for edge in kept_edges
    }

    return TopologyGraph(
        nodes=kept_nodes,
        edges=kept_edges,
        node_weights=kept_node_weights,
        edge_weights=kept_edge_weights,
    )


def prune_edges_below_weight(
    graph: TopologyGraph,
    min_edge_weight: int,
) -> TopologyGraph:
    """Remove edges below a minimum weight."""
    kept_edges = tuple(
        edge
        for edge in graph.edges
        if graph.edge_weights.get(edge, 0) >= min_edge_weight
    )

    active_nodes = set()
    for source, target in kept_edges:
        active_nodes.add(source)
        active_nodes.add(target)

    kept_nodes = tuple(
        node
        for node in graph.nodes
        if node in active_nodes
    )

    kept_node_weights: dict[Node, int] = {
        node: graph.node_weights[node]
        for node in kept_nodes
    }

    kept_edge_weights: dict[Edge, int] = {
        edge: graph.edge_weights[edge]
        for edge in kept_edges
    }

    return TopologyGraph(
        nodes=kept_nodes,
        edges=kept_edges,
        node_weights=kept_node_weights,
        edge_weights=kept_edge_weights,
    )