"""Node and edge weight utilities for topology graphs."""

from atlas.topology.graph import Edge, Node, TopologyGraph


def get_node_weight(graph: TopologyGraph, node: Node) -> int:
    """Return node weight, defaulting to zero if absent."""
    return graph.node_weights.get(node, 0)


def get_edge_weight(graph: TopologyGraph, edge: Edge) -> int:
    """Return edge weight, defaulting to zero if absent."""
    return graph.edge_weights.get(edge, 0)


def repeated_nodes(graph: TopologyGraph) -> dict[Node, int]:
    """Return nodes with weight greater than one."""
    return {
        node: weight
        for node, weight in graph.node_weights.items()
        if weight > 1
    }


def repeated_edges(graph: TopologyGraph) -> dict[Edge, int]:
    """Return edges with weight greater than one."""
    return {
        edge: weight
        for edge, weight in graph.edge_weights.items()
        if weight > 1
    }


def node_depth(graph: TopologyGraph, node: Node) -> int:
    """Return Z-axis depth for a node.

    A node visited once has depth 1.
    Repeated visits increase depth.
    """
    return get_node_weight(graph, node)


def edge_reinforcement(graph: TopologyGraph, edge: Edge) -> int:
    """Return reinforcement strength for a directed edge."""
    return get_edge_weight(graph, edge)


def max_node_weight(graph: TopologyGraph) -> int:
    """Return the highest node weight in the graph."""
    if not graph.node_weights:
        return 0

    return max(graph.node_weights.values())


def max_edge_weight(graph: TopologyGraph) -> int:
    """Return the highest edge weight in the graph."""
    if not graph.edge_weights:
        return 0

    return max(graph.edge_weights.values())


def normalized_node_weights(graph: TopologyGraph) -> dict[Node, float]:
    """Normalize node weights into a 0.0-1.0 range."""
    max_weight = max_node_weight(graph)

    if max_weight == 0:
        return {}

    return {
        node: weight / max_weight
        for node, weight in graph.node_weights.items()
    }


def normalized_edge_weights(graph: TopologyGraph) -> dict[Edge, float]:
    """Normalize edge weights into a 0.0-1.0 range."""
    max_weight = max_edge_weight(graph)

    if max_weight == 0:
        return {}

    return {
        edge: weight / max_weight
        for edge, weight in graph.edge_weights.items()
    }