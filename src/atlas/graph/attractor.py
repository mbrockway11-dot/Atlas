"""Structural attractor extraction for Atlas IdentityGraph v2.

The Structural Attractor is the maximal coherent subgraph that survives
structural reduction. It is not the highest-weight node and it is not a
resonance score. It is a deterministic graph object derived from the reduced
IdentityGraph.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from atlas.graph.analysis import analyze_identity_graph, build_undirected_adjacency
from atlas.graph.coherence import compute_coherence_field


def extract_structural_attractor(
    graph: dict[str, Any],
    coherence_field: dict[str, Any] | None = None,
    motifs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract the structural attractor from a reduced IdentityGraph."""
    coherent_graph = _coherent_graph(graph)

    if not coherent_graph["nodes"]:
        return _empty_attractor(graph, motifs)

    components = _connected_components(coherent_graph)
    ranked_components = sorted(
        (_component_summary(coherent_graph, component) for component in components),
        key=lambda item: (
            item["mean_node_coherence"],
            item["mean_edge_coherence"],
            item["node_count"],
            item["edge_count"],
            item["total_node_weight"],
        ),
        reverse=True,
    )

    selected = ranked_components[0]
    node_ids = set(selected["nodes"])
    edge_ids = {
        edge_id
        for edge_id, edge in coherent_graph["edges"].items()
        if edge["source"] in node_ids and edge["target"] in node_ids
    }

    nodes = {
        node_id: coherent_graph["nodes"][node_id]
        for node_id in sorted(node_ids, key=_natural_key)
    }
    edges = {
        edge_id: coherent_graph["edges"][edge_id]
        for edge_id in sorted(edge_ids, key=_natural_key)
    }

    attractor_graph = {
        "name": coherent_graph.get("name"),
        "version": "structural-attractor-1.0",
        "nodes": nodes,
        "edges": edges,
        "construction_passes": list(coherent_graph.get("construction_passes", [])),
        "summary": {},
    }

    analyzed_attractor = analyze_identity_graph(attractor_graph)

    summary = _build_attractor_summary(
        source_graph=coherent_graph,
        attractor_graph=analyzed_attractor,
        component_summary=selected,
        component_count=len(components),
        motifs=motifs,
    )

    analyzed_attractor["summary"] = summary

    return {
        "version": "1.0",
        "definition": "Maximal coherent connected subgraph surviving structural reduction.",
        "selection_rule": (
            "Rank surviving connected components by mean node coherence, "
            "then mean edge coherence, size, edge count, and total node weight."
        ),
        "nodes": nodes,
        "edges": edges,
        "graph": analyzed_attractor,
        "summary": summary,
        "components_considered": ranked_components,
    }


def _coherent_graph(graph: dict[str, Any]) -> dict[str, Any]:
    has_node_coherence = all(
        "coherence" in node for node in graph.get("nodes", {}).values()
    )
    has_edge_coherence = all(
        "coherence" in edge for edge in graph.get("edges", {}).values()
    )

    if graph.get("coherence") and has_node_coherence and has_edge_coherence:
        return graph

    return compute_coherence_field(graph)


def _connected_components(graph: dict[str, Any]) -> list[set[str]]:
    adjacency = build_undirected_adjacency(graph)
    unvisited = set(graph.get("nodes", {}))
    components: list[set[str]] = []

    while unvisited:
        start = min(unvisited, key=_natural_key)
        queue: deque[str] = deque([start])
        component: set[str] = set()
        unvisited.remove(start)

        while queue:
            node_id = queue.popleft()
            component.add(node_id)

            for neighbor in sorted(adjacency.get(node_id, set()), key=_natural_key):
                if neighbor in unvisited:
                    unvisited.remove(neighbor)
                    queue.append(neighbor)

        components.append(component)

    return components


def _component_summary(
    graph: dict[str, Any],
    component: set[str],
) -> dict[str, Any]:
    nodes = [graph["nodes"][node_id] for node_id in component]
    edges = [
        edge
        for edge in graph.get("edges", {}).values()
        if edge["source"] in component and edge["target"] in component
    ]

    node_scores = [
        node.get("coherence", {}).get("score", 0.0)
        for node in nodes
    ]
    edge_scores = [
        edge.get("coherence", {}).get("score", 0.0)
        for edge in edges
    ]

    return {
        "nodes": sorted(component, key=_natural_key),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "mean_node_coherence": _mean(node_scores),
        "mean_edge_coherence": _mean(edge_scores),
        "total_node_weight": sum(node.get("weight", 0) for node in nodes),
        "total_edge_weight": sum(edge.get("weight", 0) for edge in edges),
        "density": _density(len(nodes), len(edges)),
    }


def _build_attractor_summary(
    source_graph: dict[str, Any],
    attractor_graph: dict[str, Any],
    component_summary: dict[str, Any],
    component_count: int,
    motifs: dict[str, Any] | None,
) -> dict[str, Any]:
    node_count = len(attractor_graph.get("nodes", {}))
    edge_count = len(attractor_graph.get("edges", {}))
    raw_node_count = len(source_graph.get("nodes", {}))
    raw_edge_count = len(source_graph.get("edges", {}))

    distances = _all_pairs_distances(attractor_graph)
    eccentricities = {
        node_id: max(distance_map.values(), default=0)
        for node_id, distance_map in distances.items()
    }

    reachable_distances = [
        distance
        for distance_map in distances.values()
        for target, distance in distance_map.items()
        if distance > 0 and target in attractor_graph.get("nodes", {})
    ]

    return {
        "node_count": node_count,
        "edge_count": edge_count,
        "source_node_count": raw_node_count,
        "source_edge_count": raw_edge_count,
        "node_retention_ratio": _ratio(node_count, raw_node_count),
        "edge_retention_ratio": _ratio(edge_count, raw_edge_count),
        "component_count_considered": component_count,
        "mean_node_coherence": component_summary["mean_node_coherence"],
        "mean_edge_coherence": component_summary["mean_edge_coherence"],
        "density": component_summary["density"],
        "diameter": max(eccentricities.values(), default=0),
        "radius": min(eccentricities.values(), default=0),
        "average_path_length": _mean(reachable_distances),
        "bridge_count": attractor_graph.get("analysis", {}).get("bridge_count", 0),
        "articulation_point_count": attractor_graph.get("analysis", {}).get(
            "articulation_point_count",
            0,
        ),
        "leaf_count": attractor_graph.get("analysis", {}).get("leaf_count", 0),
        "hub_count": attractor_graph.get("analysis", {}).get("hub_count", 0),
        "motif_summary": (motifs or {}).get("summary", {}),
    }


def _all_pairs_distances(graph: dict[str, Any]) -> dict[str, dict[str, int]]:
    adjacency = build_undirected_adjacency(graph)
    distances: dict[str, dict[str, int]] = {}

    for start in sorted(graph.get("nodes", {}), key=_natural_key):
        queue: deque[tuple[str, int]] = deque([(start, 0)])
        seen = {start}
        distances[start] = {start: 0}

        while queue:
            node_id, distance = queue.popleft()

            for neighbor in sorted(adjacency.get(node_id, set()), key=_natural_key):
                if neighbor not in seen:
                    seen.add(neighbor)
                    distances[start][neighbor] = distance + 1
                    queue.append((neighbor, distance + 1))

    return distances


def _empty_attractor(
    graph: dict[str, Any],
    motifs: dict[str, Any] | None,
) -> dict[str, Any]:
    summary = {
        "node_count": 0,
        "edge_count": 0,
        "source_node_count": len(graph.get("nodes", {})),
        "source_edge_count": len(graph.get("edges", {})),
        "node_retention_ratio": 0.0,
        "edge_retention_ratio": 0.0,
        "component_count_considered": 0,
        "mean_node_coherence": 0.0,
        "mean_edge_coherence": 0.0,
        "density": 0.0,
        "diameter": 0,
        "radius": 0,
        "average_path_length": 0.0,
        "bridge_count": 0,
        "articulation_point_count": 0,
        "leaf_count": 0,
        "hub_count": 0,
        "motif_summary": (motifs or {}).get("summary", {}),
    }

    empty_graph = {
        "name": graph.get("name"),
        "version": "structural-attractor-1.0",
        "nodes": {},
        "edges": {},
        "construction_passes": list(graph.get("construction_passes", [])),
        "summary": summary,
        "analysis": {
            "component_count": 0,
            "largest_component_size": 0,
            "bridge_count": 0,
            "articulation_point_count": 0,
            "leaf_count": 0,
            "hub_count": 0,
        },
    }

    return {
        "version": "1.0",
        "definition": "Maximal coherent connected subgraph surviving structural reduction.",
        "selection_rule": "No surviving nodes.",
        "nodes": {},
        "edges": {},
        "graph": empty_graph,
        "summary": summary,
        "components_considered": [],
    }


def _density(node_count: int, edge_count: int) -> float:
    if node_count <= 1:
        return 0.0

    possible_edges = node_count * (node_count - 1) / 2
    return _ratio(edge_count, possible_edges)


def _ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0

    return round(float(numerator) / float(denominator), 6)


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0

    return round(sum(values) / len(values), 6)


def _natural_key(value: Any) -> tuple[int, Any]:
    text = str(value)

    try:
        return (0, int(text))
    except ValueError:
        return (1, text)