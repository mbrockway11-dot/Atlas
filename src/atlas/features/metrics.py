"""Feature metrics for topology graphs."""

from atlas.topology.graph import Edge, Node, TopologyGraph


def node_count(graph: TopologyGraph) -> int:
    """Return number of unique active nodes."""
    return graph.node_count


def edge_count(graph: TopologyGraph) -> int:
    """Return number of unique active edges."""
    return graph.edge_count


def unique_nodes(graph: TopologyGraph) -> tuple[Node, ...]:
    """Return all unique active nodes."""
    return graph.nodes


def unique_edges(graph: TopologyGraph) -> tuple[Edge, ...]:
    """Return all unique active edges."""
    return graph.edges


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


def edge_density(graph: TopologyGraph) -> float:
    """Return directed graph edge density."""
    n = graph.node_count

    if n <= 1:
        return 0.0

    max_edges = n * (n - 1)
    return graph.edge_count / max_edges


def in_degree(graph: TopologyGraph) -> dict[Node, int]:
    """Return unweighted in-degree for each node."""
    degrees = {node: 0 for node in graph.nodes}

    for _, target in graph.edges:
        degrees[target] += 1

    return degrees


def out_degree(graph: TopologyGraph) -> dict[Node, int]:
    """Return unweighted out-degree for each node."""
    degrees = {node: 0 for node in graph.nodes}

    for source, _ in graph.edges:
        degrees[source] += 1

    return degrees


def weighted_in_degree(graph: TopologyGraph) -> dict[Node, int]:
    """Return weighted in-degree for each node."""
    degrees = {node: 0 for node in graph.nodes}

    for edge in graph.edges:
        _, target = edge
        degrees[target] += graph.edge_weights.get(edge, 0)

    return degrees


def weighted_out_degree(graph: TopologyGraph) -> dict[Node, int]:
    """Return weighted out-degree for each node."""
    degrees = {node: 0 for node in graph.nodes}

    for edge in graph.edges:
        source, _ = edge
        degrees[source] += graph.edge_weights.get(edge, 0)

    return degrees


def connected_components(graph: TopologyGraph) -> tuple[tuple[Node, ...], ...]:
    """Return weakly connected components.

    Direction is ignored for component discovery.
    Component order follows first appearance in graph.nodes.
    """
    unvisited = set(graph.nodes)
    components: list[tuple[Node, ...]] = []

    adjacency = _undirected_adjacency(graph)

    for start in graph.nodes:
        if start not in unvisited:
            continue

        component = _walk_component(start, adjacency)
        unvisited -= component

        ordered_component = tuple(
            node for node in graph.nodes
            if node in component
        )
        components.append(ordered_component)

    return tuple(components)


def graph_symmetry(graph: TopologyGraph) -> float:
    """Return ratio of edges that have a reverse counterpart."""
    if graph.edge_count == 0:
        return 0.0

    edge_set = set(graph.edges)
    reciprocal_count = 0

    for source, target in graph.edges:
        if (target, source) in edge_set:
            reciprocal_count += 1

    return reciprocal_count / graph.edge_count


def _undirected_adjacency(graph: TopologyGraph) -> dict[Node, set[Node]]:
    """Build undirected adjacency map."""
    adjacency = {node: set() for node in graph.nodes}

    for source, target in graph.edges:
        adjacency[source].add(target)
        adjacency[target].add(source)

    return adjacency


def _walk_component(
    start: Node,
    adjacency: dict[Node, set[Node]],
) -> set[Node]:
    """Walk one connected component."""
    visited = set()
    stack = [start]

    while stack:
        node = stack.pop()

        if node in visited:
            continue

        visited.add(node)

        for neighbor in adjacency[node]:
            if neighbor not in visited:
                stack.append(neighbor)

    return visited