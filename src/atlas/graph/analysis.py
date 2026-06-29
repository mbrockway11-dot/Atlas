"""Graph analysis utilities for Atlas IdentityGraph v2."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


def analyze_identity_graph(
    graph: dict[str, Any],
) -> dict[str, Any]:
    """Return an enriched copy of an IdentityGraph with structural analysis."""
    analyzed = copy_graph(graph)

    adjacency = build_undirected_adjacency(analyzed)
    directed = build_directed_adjacency(analyzed)

    attach_degree_metrics(analyzed, adjacency, directed)
    components = connected_components(adjacency)
    attach_components(analyzed, components)

    bridges = find_bridges(adjacency)
    articulations = find_articulation_points(adjacency)

    attach_bridge_flags(analyzed, bridges)
    attach_articulation_flags(analyzed, articulations)
    attach_leaf_and_hub_flags(analyzed)

    analyzed["analysis"] = {
        "component_count": len(components),
        "largest_component_size": max((len(c) for c in components), default=0),
        "bridge_count": len(bridges),
        "articulation_point_count": len(articulations),
        "leaf_count": count_flag(analyzed["nodes"].values(), "is_leaf"),
        "hub_count": count_flag(analyzed["nodes"].values(), "is_hub"),
    }

    return analyzed


def copy_graph(graph: dict[str, Any]) -> dict[str, Any]:
    """Make a safe JSON-like graph copy."""
    return {
        "name": graph["name"],
        "version": graph["version"],
        "nodes": {
            key: dict(value)
            for key, value in graph["nodes"].items()
        },
        "edges": {
            key: dict(value)
            for key, value in graph["edges"].items()
        },
        "construction_passes": list(graph["construction_passes"]),
        "summary": dict(graph["summary"]),
    }


def build_undirected_adjacency(
    graph: dict[str, Any],
) -> dict[str, set[str]]:
    """Build undirected adjacency map."""
    adjacency: dict[str, set[str]] = {
        node_id: set()
        for node_id in graph["nodes"]
    }

    for edge in graph["edges"].values():
        source = edge["source"]
        target = edge["target"]

        adjacency.setdefault(source, set()).add(target)
        adjacency.setdefault(target, set()).add(source)

    return adjacency


def build_directed_adjacency(
    graph: dict[str, Any],
) -> dict[str, dict[str, set[str]]]:
    """Build directed adjacency map."""
    directed = {
        node_id: {
            "in": set(),
            "out": set(),
        }
        for node_id in graph["nodes"]
    }

    for edge in graph["edges"].values():
        source = edge["source"]
        target = edge["target"]

        directed.setdefault(source, {"in": set(), "out": set()})
        directed.setdefault(target, {"in": set(), "out": set()})

        directed[source]["out"].add(target)
        directed[target]["in"].add(source)

    return directed


def attach_degree_metrics(
    graph: dict[str, Any],
    adjacency: dict[str, set[str]],
    directed: dict[str, dict[str, set[str]]],
) -> None:
    """Attach degree metrics to nodes."""
    for node_id, node in graph["nodes"].items():
        node["neighbors"] = sorted(adjacency.get(node_id, set()))
        node["degree"] = len(node["neighbors"])
        node["in_neighbors"] = sorted(directed[node_id]["in"])
        node["out_neighbors"] = sorted(directed[node_id]["out"])
        node["in_degree"] = len(node["in_neighbors"])
        node["out_degree"] = len(node["out_neighbors"])


def connected_components(
    adjacency: dict[str, set[str]],
) -> list[set[str]]:
    """Find connected components in undirected graph."""
    seen: set[str] = set()
    components: list[set[str]] = []

    for node in adjacency:
        if node in seen:
            continue

        component: set[str] = set()
        queue = deque([node])
        seen.add(node)

        while queue:
            current = queue.popleft()
            component.add(current)

            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)

        components.append(component)

    return components


def attach_components(
    graph: dict[str, Any],
    components: list[set[str]],
) -> None:
    """Attach component ids to nodes."""
    for component_id, component in enumerate(components):
        for node_id in component:
            graph["nodes"][node_id]["component"] = component_id
            graph["nodes"][node_id]["component_size"] = len(component)


def find_bridges(
    adjacency: dict[str, set[str]],
) -> set[tuple[str, str]]:
    """Find bridges in an undirected graph using DFS low-link."""
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

        for neighbor in adjacency[node]:
            if neighbor not in visited:
                parent[neighbor] = node
                dfs(neighbor)

                low[node] = min(low[node], low[neighbor])

                if low[neighbor] > discovery[node]:
                    bridges.add(normalize_edge(node, neighbor))

            elif neighbor != parent.get(node):
                low[node] = min(low[node], discovery[neighbor])

    for node in adjacency:
        if node not in visited:
            parent[node] = None
            dfs(node)

    return bridges


def find_articulation_points(
    adjacency: dict[str, set[str]],
) -> set[str]:
    """Find articulation points in an undirected graph."""
    visited: set[str] = set()
    discovery: dict[str, int] = {}
    low: dict[str, int] = {}
    parent: dict[str, str | None] = {}
    articulations: set[str] = set()
    time = 0

    def dfs(node: str) -> None:
        nonlocal time

        children = 0
        visited.add(node)
        discovery[node] = time
        low[node] = time
        time += 1

        for neighbor in adjacency[node]:
            if neighbor not in visited:
                parent[neighbor] = node
                children += 1
                dfs(neighbor)

                low[node] = min(low[node], low[neighbor])

                if parent.get(node) is None and children > 1:
                    articulations.add(node)

                if parent.get(node) is not None and low[neighbor] >= discovery[node]:
                    articulations.add(node)

            elif neighbor != parent.get(node):
                low[node] = min(low[node], discovery[neighbor])

    for node in adjacency:
        if node not in visited:
            parent[node] = None
            dfs(node)

    return articulations


def attach_bridge_flags(
    graph: dict[str, Any],
    bridges: set[tuple[str, str]],
) -> None:
    """Attach bridge flags to edges."""
    for edge in graph["edges"].values():
        normalized = normalize_edge(edge["source"], edge["target"])
        edge["is_bridge"] = normalized in bridges


def attach_articulation_flags(
    graph: dict[str, Any],
    articulations: set[str],
) -> None:
    """Attach articulation flags to nodes."""
    for node_id, node in graph["nodes"].items():
        node["is_articulation"] = node_id in articulations


def attach_leaf_and_hub_flags(
    graph: dict[str, Any],
) -> None:
    """Attach leaf and hub flags to nodes."""
    degrees = [
        node["degree"]
        for node in graph["nodes"].values()
    ]

    if not degrees:
        return

    average_degree = sum(degrees) / len(degrees)

    for node in graph["nodes"].values():
        node["is_leaf"] = node["degree"] <= 1
        node["is_hub"] = node["degree"] > average_degree and node["degree"] >= 3


def normalize_edge(source: str, target: str) -> tuple[str, str]:
    """Normalize undirected edge identity."""
    return tuple(sorted([source, target]))


def count_flag(records, key: str) -> int:
    """Count records where flag is true."""
    return len([record for record in records if record.get(key)])