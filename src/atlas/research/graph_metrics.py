"""Graph metric extraction for Atlas research rows."""

from __future__ import annotations

from collections import deque
from statistics import mean, pstdev
from typing import Any


def build_layer_graph_metrics(layer: dict[str, Any]) -> dict[str, Any]:
    """Build graph-theoretic metrics for one construction layer."""
    path = layer["features"]["path_views"]["analysis_path"]
    visits = path["visit_history"]["visits"]

    nodes = {
        str(visit["node"])
        for visit in visits
    }

    directed_edges = [
        (
            str(source["node"]),
            str(target["node"]),
        )
        for source, target in zip(visits[:-1], visits[1:])
    ]

    adjacency = build_undirected_adjacency(
        nodes=nodes,
        directed_edges=directed_edges,
    )

    component_sizes = connected_component_sizes(
        nodes=nodes,
        adjacency=adjacency,
    )

    largest_component_size = max(component_sizes, default=0)

    degrees = [
        len(adjacency[node])
        for node in nodes
    ]

    node_count = len(nodes)

    undirected_edges = {
        tuple(sorted((source, target)))
        for source, target in directed_edges
        if source != target
    }

    edge_count = len(undirected_edges)

    hubs = {
        node
        for node in nodes
        if len(adjacency[node]) >= 3
    }

    leaves = {
        node
        for node in nodes
        if len(adjacency[node]) == 1
    }

    bridges = find_bridges(nodes, adjacency)
    articulations = find_articulation_points(nodes, adjacency)

    return {
        "component_count": len(component_sizes),
        "largest_component_size": largest_component_size,
        "largest_component_ratio": safe_ratio(
            largest_component_size,
            node_count,
        ),
        "mean_degree": mean(degrees) if degrees else 0.0,
        "max_degree": max(degrees, default=0),
        "degree_std": pstdev(degrees) if len(degrees) > 1 else 0.0,
        "hub_count": len(hubs),
        "hub_ratio": safe_ratio(len(hubs), node_count),
        "leaf_count": len(leaves),
        "leaf_ratio": safe_ratio(len(leaves), node_count),
        "bridge_count": len(bridges),
        "bridge_ratio": safe_ratio(len(bridges), edge_count),
        "articulation_count": len(articulations),
        "articulation_ratio": safe_ratio(len(articulations), node_count),
    }


def build_undirected_adjacency(
    nodes: set[str],
    directed_edges: list[tuple[str, str]],
) -> dict[str, set[str]]:
    """Build undirected adjacency from directed construction edges."""
    adjacency = {
        node: set()
        for node in nodes
    }

    for source, target in directed_edges:
        if source == target:
            continue

        adjacency.setdefault(source, set()).add(target)
        adjacency.setdefault(target, set()).add(source)

    return adjacency


def connected_component_sizes(
    nodes: set[str],
    adjacency: dict[str, set[str]],
) -> list[int]:
    """Return connected component sizes."""
    unseen = set(nodes)
    sizes = []

    while unseen:
        start = min(unseen)
        queue = deque([start])
        unseen.remove(start)
        size = 0

        while queue:
            node = queue.popleft()
            size += 1

            for neighbor in sorted(adjacency[node]):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)

        sizes.append(size)

    return sizes


def find_bridges(
    nodes: set[str],
    adjacency: dict[str, set[str]],
) -> set[tuple[str, str]]:
    """Find undirected graph bridges using DFS low-link analysis."""
    visited: set[str] = set()
    discovery: dict[str, int] = {}
    low: dict[str, int] = {}
    parent: dict[str, str | None] = {}
    bridges: set[tuple[str, str]] = set()
    time = 0

    def dfs(node: str) -> None:
        nonlocal time

        visited.add(node)
        discovery[node] = time
        low[node] = time
        time += 1

        for neighbor in sorted(adjacency[node]):
            if neighbor not in visited:
                parent[neighbor] = node
                dfs(neighbor)

                low[node] = min(low[node], low[neighbor])

                if low[neighbor] > discovery[node]:
                    bridges.add(tuple(sorted((node, neighbor))))

            elif neighbor != parent.get(node):
                low[node] = min(low[node], discovery[neighbor])

    for node in sorted(nodes):
        if node not in visited:
            parent[node] = None
            dfs(node)

    return bridges


def find_articulation_points(
    nodes: set[str],
    adjacency: dict[str, set[str]],
) -> set[str]:
    """Find articulation points using DFS low-link analysis."""
    visited: set[str] = set()
    discovery: dict[str, int] = {}
    low: dict[str, int] = {}
    parent: dict[str, str | None] = {}
    articulations: set[str] = set()
    time = 0

    def dfs(node: str) -> None:
        nonlocal time

        visited.add(node)
        discovery[node] = time
        low[node] = time
        time += 1

        child_count = 0

        for neighbor in sorted(adjacency[node]):
            if neighbor not in visited:
                parent[neighbor] = node
                child_count += 1
                dfs(neighbor)

                low[node] = min(low[node], low[neighbor])

                if parent[node] is None and child_count > 1:
                    articulations.add(node)

                if parent[node] is not None and low[neighbor] >= discovery[node]:
                    articulations.add(node)

            elif neighbor != parent.get(node):
                low[node] = min(low[node], discovery[neighbor])

    for node in sorted(nodes):
        if node not in visited:
            parent[node] = None
            dfs(node)

    return articulations


def safe_ratio(numerator: float, denominator: float) -> float:
    """Safely divide two values."""
    if denominator == 0:
        return 0.0

    return float(numerator) / float(denominator)