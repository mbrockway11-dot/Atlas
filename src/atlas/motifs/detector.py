"""Deterministic motif detection for topology graphs."""

from atlas.features.metrics import in_degree, out_degree
from atlas.motifs.catalog import MotifCounts
from atlas.topology.graph import Edge, Node, TopologyGraph


def detect_motifs(graph: TopologyGraph) -> MotifCounts:
    """Detect core graph motifs."""
    in_degrees = in_degree(graph)
    out_degrees = out_degree(graph)

    return MotifCounts(
        chains=count_chain_nodes(graph, in_degrees, out_degrees),
        hubs=count_hubs(graph, out_degrees),
        loops=count_self_loops(graph),
        bridges=count_bridge_edges(graph),
        dead_ends=count_dead_ends(graph, in_degrees, out_degrees),
        reciprocal_pairs=count_reciprocal_pairs(graph),
        isolated_nodes=count_isolated_nodes(graph, in_degrees, out_degrees),
    )


def count_chain_nodes(
    graph: TopologyGraph,
    in_degrees: dict[Node, int] | None = None,
    out_degrees: dict[Node, int] | None = None,
) -> int:
    """Count nodes that behave like chain pass-through points."""
    if in_degrees is None:
        in_degrees = in_degree(graph)

    if out_degrees is None:
        out_degrees = out_degree(graph)

    return sum(
        1
        for node in graph.nodes
        if in_degrees.get(node, 0) == 1 and out_degrees.get(node, 0) == 1
    )


def count_hubs(
    graph: TopologyGraph,
    out_degrees: dict[Node, int] | None = None,
    threshold: int = 3,
) -> int:
    """Count outward hub nodes."""
    if out_degrees is None:
        out_degrees = out_degree(graph)

    return sum(
        1
        for node in graph.nodes
        if out_degrees.get(node, 0) >= threshold
    )


def count_self_loops(graph: TopologyGraph) -> int:
    """Count edges where source and target are the same node."""
    return sum(
        1
        for source, target in graph.edges
        if source == target
    )


def count_reciprocal_pairs(graph: TopologyGraph) -> int:
    """Count reciprocal edge pairs once."""
    edge_set = set(graph.edges)
    counted: set[Edge] = set()
    total = 0

    for source, target in graph.edges:
        edge = (source, target)
        reverse = (target, source)

        if edge in counted or reverse in counted:
            continue

        if reverse in edge_set and source != target:
            total += 1
            counted.add(edge)
            counted.add(reverse)

    return total


def count_dead_ends(
    graph: TopologyGraph,
    in_degrees: dict[Node, int] | None = None,
    out_degrees: dict[Node, int] | None = None,
) -> int:
    """Count nodes that receive flow but do not emit flow."""
    if in_degrees is None:
        in_degrees = in_degree(graph)

    if out_degrees is None:
        out_degrees = out_degree(graph)

    return sum(
        1
        for node in graph.nodes
        if in_degrees.get(node, 0) > 0 and out_degrees.get(node, 0) == 0
    )


def count_isolated_nodes(
    graph: TopologyGraph,
    in_degrees: dict[Node, int] | None = None,
    out_degrees: dict[Node, int] | None = None,
) -> int:
    """Count nodes with no incoming or outgoing edges."""
    if in_degrees is None:
        in_degrees = in_degree(graph)

    if out_degrees is None:
        out_degrees = out_degree(graph)

    return sum(
        1
        for node in graph.nodes
        if in_degrees.get(node, 0) == 0 and out_degrees.get(node, 0) == 0
    )


def count_bridge_edges(graph: TopologyGraph) -> int:
    """Count weak bridge edges.

    A bridge edge is approximated as an edge whose removal increases
    weakly connected component count.
    """
    if not graph.edges:
        return 0

    original_count = _component_count(graph.nodes, graph.edges)
    bridge_count = 0

    for removed_edge in graph.edges:
        remaining_edges = tuple(
            edge for edge in graph.edges
            if edge != removed_edge
        )

        new_count = _component_count(graph.nodes, remaining_edges)

        if new_count > original_count:
            bridge_count += 1

    return bridge_count


def _component_count(
    nodes: tuple[Node, ...],
    edges: tuple[Edge, ...],
) -> int:
    """Count weakly connected components from raw nodes and edges."""
    if not nodes:
        return 0

    adjacency = {node: set() for node in nodes}

    for source, target in edges:
        adjacency[source].add(target)
        adjacency[target].add(source)

    unvisited = set(nodes)
    count = 0

    for start in nodes:
        if start not in unvisited:
            continue

        count += 1
        stack = [start]

        while stack:
            node = stack.pop()

            if node not in unvisited:
                continue

            unvisited.remove(node)

            for neighbor in adjacency[node]:
                if neighbor in unvisited:
                    stack.append(neighbor)

    return count