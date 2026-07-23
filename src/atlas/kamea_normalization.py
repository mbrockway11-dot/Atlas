"""Normalize differently sized Kamea paths into weighted unit-space graphs."""

from __future__ import annotations

from collections import Counter, defaultdict, deque
import math
from typing import Any

from atlas.kamea_flow.flow import build_kamea_flow


NORMALIZED_KAMEA_GRAPH_VERSION = "1.1.0"
CLASSICAL_KAMEA_BODIES = (
    "saturn", "jupiter", "mars", "sun", "venus", "mercury", "moon",
)
ASTRONOMY_ONLY_BODIES = ("uranus", "neptune", "pluto")


def build_normalized_kamea_graphs(payload: dict[str, Any]) -> dict[str, Any]:
    """Collapse repeated geometry into node/edge weights for every planet."""
    flow = build_kamea_flow(payload)
    streams: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for step in flow.get("steps", []):
        streams[str(step.get("stream_id"))].append(step)

    by_planet: dict[str, list[list[dict[str, Any]]]] = defaultdict(list)
    for rows in streams.values():
        ordered = sorted(rows, key=lambda row: row.get("stream_index", 0))
        if ordered:
            by_planet[str(ordered[0].get("planet")).strip().casefold()].append(
                ordered
            )

    graphs = {
        planet: build_weighted_graph(planet, planet_streams)
        for planet, planet_streams in sorted(by_planet.items())
        if planet.casefold() in CLASSICAL_KAMEA_BODIES
    }
    excluded_planets = sorted(
        planet
        for planet in by_planet
        if planet.casefold() not in CLASSICAL_KAMEA_BODIES
    )
    return {
        "success": True,
        "version": NORMALIZED_KAMEA_GRAPH_VERSION,
        "coordinate_system": "unit_square_[0,1]",
        "normalization": "x/(n-1), y/(n-1)",
        "geometry_deduplicated": True,
        "repeated_nodes_increase_weight": True,
        "repeated_edges_increase_weight": True,
        "graphs": graphs,
        "classical_kamea_bodies": list(CLASSICAL_KAMEA_BODIES),
        "astronomy_only_bodies": list(ASTRONOMY_ONLY_BODIES),
        "projection_registry": {
            body: {
                "available": True,
                "basis": "historical_classical_kamea",
                "generated": body in graphs,
            }
            for body in CLASSICAL_KAMEA_BODIES
        } | {
            body: {
                "available": False,
                "reason": "no_historical_classical_kamea",
                "generated": False,
            }
            for body in ASTRONOMY_ONLY_BODIES
        },
        "excluded_nonclassical_streams": excluded_planets,
        "summary": {
            "historically_supported_planet_count": len(CLASSICAL_KAMEA_BODIES),
            "planet_count": len(graphs),
            "node_count": sum(row["node_count"] for row in graphs.values()),
            "edge_count": sum(row["edge_count"] for row in graphs.values()),
        },
        "interpretation_applied": False,
    }


def build_weighted_graph(
    planet: str,
    streams: list[list[dict[str, Any]]],
) -> dict[str, Any]:
    node_weights: Counter[tuple[float, float]] = Counter()
    edge_weights: Counter[
        tuple[tuple[float, float], tuple[float, float]]
    ] = Counter()
    grid_sizes = set()
    for stream in streams:
        coordinates = []
        for step in stream:
            coordinate = (
                round(float(step.get("normalized_x") or 0.0), 6),
                round(float(step.get("normalized_y") or 0.0), 6),
            )
            node_weights[coordinate] += 1
            coordinates.append(coordinate)
            grid_sizes.add(int(step.get("grid_size") or 0))
        edge_weights.update(zip(coordinates, coordinates[1:]))

    ordered_nodes = sorted(node_weights)
    node_ids = {coordinate: f"n{index}" for index, coordinate in enumerate(ordered_nodes)}
    nodes = [
        {
            "node_id": node_ids[coordinate],
            "x": coordinate[0],
            "y": coordinate[1],
            "weight": node_weights[coordinate],
        }
        for coordinate in ordered_nodes
    ]
    edges = [
        {
            "source": node_ids[source],
            "target": node_ids[target],
            "weight": weight,
        }
        for (source, target), weight in sorted(edge_weights.items())
    ]
    metrics = graph_metrics(nodes, edges)
    return {
        "planet": planet,
        "source_grid_sizes": sorted(grid_sizes),
        "stream_count": len(streams),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "metrics": metrics,
    }


def graph_metrics(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    node_count = len(nodes)
    edge_count = len(edges)
    visits = sum(int(row["weight"]) for row in nodes)
    transitions = sum(int(row["weight"]) for row in edges)
    adjacency: dict[str, set[str]] = {row["node_id"]: set() for row in nodes}
    weighted_degree: Counter[str] = Counter()
    self_loops = 0
    directed = set()
    for edge in edges:
        source, target = edge["source"], edge["target"]
        weight = int(edge["weight"])
        directed.add((source, target))
        adjacency[source].add(target)
        adjacency[target].add(source)
        weighted_degree[source] += weight
        weighted_degree[target] += weight
        self_loops += source == target

    degrees = [len(adjacency[node]) for node in adjacency]
    clustering = mean(local_clustering(node, adjacency) for node in adjacency)
    diameter, average_path = path_metrics(adjacency)
    weights = [int(row["weight"]) for row in nodes]
    center_x = sum(float(row["x"]) * int(row["weight"]) for row in nodes) / visits if visits else 0.0
    center_y = sum(float(row["y"]) * int(row["weight"]) for row in nodes) / visits if visits else 0.0
    coordinate_set = {(float(row["x"]), float(row["y"])) for row in nodes}
    reciprocal = sum((b, a) in directed for a, b in directed if a != b) // 2
    triangles = triangle_count(adjacency)

    return {
        "node_coverage": round(node_count / visits, 6) if visits else 0.0,
        "edge_density": round(edge_count / (node_count * node_count), 6) if node_count else 0.0,
        "loop_density": round(self_loops / edge_count, 6) if edge_count else 0.0,
        "hub_ratio": round(max(weighted_degree.values(), default=0) / max(sum(weighted_degree.values()), 1), 6),
        "branching_factor": round(mean(len(adjacency[node]) for node in adjacency), 6),
        "average_degree": round(mean(degrees), 6),
        "clustering_coefficient": round(clustering, 6),
        "graph_diameter": diameter,
        "average_path_length": round(average_path, 6),
        "entropy": round(normalized_entropy(weights), 6),
        "reflection_symmetry_vertical": symmetry_ratio(coordinate_set, lambda x, y: (1.0 - x, y)),
        "reflection_symmetry_horizontal": symmetry_ratio(coordinate_set, lambda x, y: (x, 1.0 - y)),
        "rotational_symmetry_180": symmetry_ratio(coordinate_set, lambda x, y: (1.0 - x, 1.0 - y)),
        "axiality": round(max(
            symmetry_ratio(coordinate_set, lambda x, y: (1.0 - x, y)),
            symmetry_ratio(coordinate_set, lambda x, y: (x, 1.0 - y)),
        ), 6),
        "center_of_mass": {"x": round(center_x, 6), "y": round(center_y, 6)},
        "revisit_intensity": round(1.0 - node_count / visits, 6) if visits else 0.0,
        "persistence_score": round(1.0 - edge_count / transitions, 6) if transitions else 0.0,
        "motif_frequency": {
            "self_loops": self_loops,
            "reciprocal_pairs": reciprocal,
            "triangles": triangles,
        },
        "betweenness_centrality": betweenness_summary(adjacency),
        "eigenvector_centrality": eigenvector_summary(adjacency),
    }


def local_clustering(node: str, adjacency: dict[str, set[str]]) -> float:
    neighbors = list(adjacency[node] - {node})
    if len(neighbors) < 2:
        return 0.0
    links = sum(b in adjacency[a] for index, a in enumerate(neighbors) for b in neighbors[index + 1:])
    return links / (len(neighbors) * (len(neighbors) - 1) / 2)


def path_metrics(adjacency: dict[str, set[str]]) -> tuple[int, float]:
    distances = []
    diameter = 0
    for start in adjacency:
        found = {start: 0}
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for neighbor in adjacency[node] - found.keys():
                found[neighbor] = found[node] + 1
                queue.append(neighbor)
        values = [distance for node, distance in found.items() if node != start]
        distances.extend(values)
        diameter = max(diameter, max(values, default=0))
    return diameter, mean(distances)


def triangle_count(adjacency: dict[str, set[str]]) -> int:
    triangles = 0
    nodes = sorted(adjacency)
    for index, left in enumerate(nodes):
        for middle in nodes[index + 1:]:
            if middle not in adjacency[left]:
                continue
            for right in nodes:
                if right > middle and right in adjacency[left] and right in adjacency[middle]:
                    triangles += 1
    return triangles


def normalized_entropy(weights: list[int]) -> float:
    total = sum(weights)
    if total <= 0 or len(weights) <= 1:
        return 0.0
    entropy = -sum((weight / total) * math.log(weight / total, 2) for weight in weights if weight)
    return entropy / math.log(len(weights), 2)


def symmetry_ratio(points: set[tuple[float, float]], transform: Any) -> float:
    if not points:
        return 0.0
    transformed = {(round(transform(x, y)[0], 6), round(transform(x, y)[1], 6)) for x, y in points}
    return round(len(points & transformed) / len(points | transformed), 6)


def betweenness_summary(adjacency: dict[str, set[str]]) -> dict[str, float]:
    scores = {node: 0.0 for node in adjacency}
    for source in adjacency:
        stack = []
        predecessors = {node: [] for node in adjacency}
        paths = dict.fromkeys(adjacency, 0.0)
        paths[source] = 1.0
        distance = dict.fromkeys(adjacency, -1)
        distance[source] = 0
        queue = deque([source])
        while queue:
            node = queue.popleft()
            stack.append(node)
            for neighbor in adjacency[node]:
                if distance[neighbor] < 0:
                    queue.append(neighbor)
                    distance[neighbor] = distance[node] + 1
                if distance[neighbor] == distance[node] + 1:
                    paths[neighbor] += paths[node]
                    predecessors[neighbor].append(node)
        dependency = dict.fromkeys(adjacency, 0.0)
        while stack:
            node = stack.pop()
            for predecessor in predecessors[node]:
                if paths[node]:
                    dependency[predecessor] += paths[predecessor] / paths[node] * (1.0 + dependency[node])
            if node != source:
                scores[node] += dependency[node]
    values = [value / 2.0 for value in scores.values()]
    return {"maximum": round(max(values, default=0.0), 6), "mean": round(mean(values), 6)}


def eigenvector_summary(adjacency: dict[str, set[str]]) -> dict[str, float]:
    if not adjacency:
        return {"maximum": 0.0, "mean": 0.0}
    scores = {node: 1.0 for node in adjacency}
    for _ in range(100):
        updated = {node: sum(scores[neighbor] for neighbor in adjacency[node]) for node in adjacency}
        norm = math.sqrt(sum(value * value for value in updated.values()))
        if not norm:
            break
        updated = {node: value / norm for node, value in updated.items()}
        if max(abs(updated[node] - scores[node]) for node in scores) < 1e-9:
            scores = updated
            break
        scores = updated
    values = list(scores.values())
    return {"maximum": round(max(values, default=0.0), 6), "mean": round(mean(values), 6)}


def mean(values: Any) -> float:
    items = list(values)
    return sum(items) / len(items) if items else 0.0


__all__ = [
    "ASTRONOMY_ONLY_BODIES",
    "CLASSICAL_KAMEA_BODIES",
    "build_normalized_kamea_graphs",
    "build_weighted_graph",
    "graph_metrics",
]
