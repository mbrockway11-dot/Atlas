"""Extended topology metrics for the identity feature vector.

The base 17-feature vector captured coverage, survival and a few structural
ratios but omitted most of the classical graph-theoretic descriptors the sigil
graph actually supports. This builder computes them directly from one identity
layer's traversal graph (``node_weights`` + ``edge_weights``) and path geometry
(``coordinates``), each mapped into ``[0, 1]`` so it can join the bounded
feature vector without a separate normalization contract.

Everything here is pure and deterministic: the graph is built with a fixed
node ordering and NumPy's symmetric eigensolver, so the same layer always
yields the same features -- which is what keeps the ACF path and the compiled
runtime bit-exact.
"""

from __future__ import annotations

from collections import deque
from typing import Any

import numpy as np


def build_layer_topology_metrics(layer: dict[str, Any]) -> dict[str, float]:
    """Return the seven extended topology features for one identity layer.

    The metrics are computed on the *undirected simple* projection of the
    traversal graph (direction collapsed, self-loops dropped), except the
    fractal dimension, which is a box-count over the ordered path coordinates.
    """
    base = layer["features"]
    path = base["path_views"]["analysis_path"]
    node_weights = path.get("node_weights", {})
    edge_weights = path.get("edge_weights", {})
    coordinates = path.get("coordinates", [])

    nodes, adjacency = _undirected_graph(node_weights, edge_weights)

    return {
        "clustering_coefficient": _clustering_coefficient(nodes, adjacency),
        "diameter_ratio": _diameter_ratio(nodes, adjacency),
        "betweenness_centralization": _betweenness_centralization(nodes, adjacency),
        "eigenvector_centralization": _eigenvector_centralization(nodes, adjacency),
        "cycle_density": _cycle_density(nodes, adjacency),
        "fractal_dimension": _fractal_dimension(coordinates),
        "spectral_radius_ratio": _spectral_radius_ratio(nodes, adjacency),
    }


def _undirected_graph(
    node_weights: dict[str, Any], edge_weights: dict[str, Any]
) -> tuple[list[str], dict[str, set[str]]]:
    """Build a sorted node list + undirected adjacency, self-loops removed."""
    nodes: set[str] = {str(node) for node in node_weights}
    adjacency: dict[str, set[str]] = {}

    for edge in edge_weights:
        source, _, target = str(edge).partition("->")
        source, target = source.strip(), target.strip()
        if not source or not target:
            continue
        nodes.add(source)
        nodes.add(target)
        if source == target:
            continue  # self-loop: carried elsewhere (loop_ratio), not structural
        adjacency.setdefault(source, set()).add(target)
        adjacency.setdefault(target, set()).add(source)

    ordered = sorted(nodes, key=_node_sort_key)
    for node in ordered:
        adjacency.setdefault(node, set())
    return ordered, adjacency


def _node_sort_key(node: str) -> tuple[int, Any]:
    """Sort numeric node ids numerically, others lexically, deterministically."""
    try:
        return (0, int(node))
    except (TypeError, ValueError):
        return (1, node)


def _clustering_coefficient(
    nodes: list[str], adjacency: dict[str, set[str]]
) -> float:
    """Average local clustering coefficient over nodes with degree >= 2."""
    coefficients = []
    for node in nodes:
        neighbors = adjacency[node]
        degree = len(neighbors)
        if degree < 2:
            continue
        links = 0
        neighbor_list = sorted(neighbors, key=_node_sort_key)
        for i, left in enumerate(neighbor_list):
            for right in neighbor_list[i + 1:]:
                if right in adjacency[left]:
                    links += 1
        coefficients.append(2.0 * links / (degree * (degree - 1)))
    return float(np.mean(coefficients)) if coefficients else 0.0


def _bfs_distances(source: str, adjacency: dict[str, set[str]]) -> dict[str, int]:
    """Shortest-path hop counts from ``source`` within its component."""
    distances = {source: 0}
    queue = deque([source])
    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current]:
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                queue.append(neighbor)
    return distances


def _diameter_ratio(nodes: list[str], adjacency: dict[str, set[str]]) -> float:
    """Diameter of the largest component / (its node count - 1)."""
    if len(nodes) < 2:
        return 0.0
    component = _largest_component(nodes, adjacency)
    if len(component) < 2:
        return 0.0
    diameter = 0
    for node in component:
        distances = _bfs_distances(node, adjacency)
        reach = max(distances[other] for other in component if other in distances)
        diameter = max(diameter, reach)
    return diameter / (len(component) - 1)


def _largest_component(
    nodes: list[str], adjacency: dict[str, set[str]]
) -> list[str]:
    seen: set[str] = set()
    best: list[str] = []
    for node in nodes:
        if node in seen:
            continue
        reached = _bfs_distances(node, adjacency)
        seen.update(reached)
        if len(reached) > len(best):
            best = sorted(reached, key=_node_sort_key)
    return best


def _component_count(nodes: list[str], adjacency: dict[str, set[str]]) -> int:
    seen: set[str] = set()
    count = 0
    for node in nodes:
        if node in seen:
            continue
        seen.update(_bfs_distances(node, adjacency))
        count += 1
    return count


def _cycle_density(nodes: list[str], adjacency: dict[str, set[str]]) -> float:
    """Cyclomatic number E - N + C, normalized by its connected maximum."""
    n = len(nodes)
    if n < 3:
        return 0.0
    edge_count = sum(len(neighbors) for neighbors in adjacency.values()) // 2
    components = _component_count(nodes, adjacency)
    cyclomatic = edge_count - n + components
    max_cyclomatic = n * (n - 1) // 2 - n + 1  # complete graph, one component
    if max_cyclomatic <= 0:
        return 0.0
    return max(0.0, cyclomatic / max_cyclomatic)


def _adjacency_matrix(
    nodes: list[str], adjacency: dict[str, set[str]]
) -> np.ndarray:
    index = {node: i for i, node in enumerate(nodes)}
    matrix = np.zeros((len(nodes), len(nodes)), dtype=float)
    for node in nodes:
        for neighbor in adjacency[node]:
            matrix[index[node], index[neighbor]] = 1.0
    return matrix


def _spectral_radius_ratio(
    nodes: list[str], adjacency: dict[str, set[str]]
) -> float:
    """Largest adjacency eigenvalue / max degree (<= 1 for any graph)."""
    if len(nodes) < 2:
        return 0.0
    max_degree = max(len(adjacency[node]) for node in nodes)
    if max_degree == 0:
        return 0.0
    matrix = _adjacency_matrix(nodes, adjacency)
    eigenvalues = np.linalg.eigvalsh(matrix)
    spectral_radius = float(np.max(np.abs(eigenvalues)))
    return min(1.0, spectral_radius / max_degree)


def _eigenvector_centralization(
    nodes: list[str], adjacency: dict[str, set[str]]
) -> float:
    """Freeman centralization of eigenvector centrality (concentration in [0,1])."""
    if len(nodes) < 3:
        return 0.0
    matrix = _adjacency_matrix(nodes, adjacency)
    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    dominant = np.abs(eigenvectors[:, int(np.argmax(eigenvalues))])
    peak = float(np.max(dominant))
    if peak <= 0.0:
        return 0.0
    scores = dominant / peak  # max node = 1.0
    return _freeman_centralization(scores)


def _betweenness_centralization(
    nodes: list[str], adjacency: dict[str, set[str]]
) -> float:
    """Freeman centralization of (normalized) Brandes betweenness, in [0,1]."""
    n = len(nodes)
    if n < 3:
        return 0.0
    betweenness = {node: 0.0 for node in nodes}
    for source in nodes:  # Brandes, unweighted
        stack: list[str] = []
        predecessors: dict[str, list[str]] = {node: [] for node in nodes}
        sigma = {node: 0.0 for node in nodes}
        distance = {node: -1 for node in nodes}
        sigma[source] = 1.0
        distance[source] = 0
        queue = deque([source])
        while queue:
            current = queue.popleft()
            stack.append(current)
            for neighbor in adjacency[current]:
                if distance[neighbor] < 0:
                    distance[neighbor] = distance[current] + 1
                    queue.append(neighbor)
                if distance[neighbor] == distance[current] + 1:
                    sigma[neighbor] += sigma[current]
                    predecessors[neighbor].append(current)
        delta = {node: 0.0 for node in nodes}
        while stack:
            node = stack.pop()
            for predecessor in predecessors[node]:
                delta[predecessor] += (
                    sigma[predecessor] / sigma[node] * (1.0 + delta[node])
                )
            if node != source:
                betweenness[node] += delta[node]
    scale = (n - 1) * (n - 2)  # undirected normalization
    scores = np.array(
        [(2.0 * betweenness[node] / scale) if scale else 0.0 for node in nodes]
    )
    return _freeman_centralization(scores)


def _freeman_centralization(scores: np.ndarray) -> float:
    """Freeman graph centralization: how concentrated a centrality is, in [0,1]."""
    n = len(scores)
    if n < 2:
        return 0.0
    peak = float(np.max(scores))
    numerator = float(np.sum(peak - scores))
    denominator = float(n - 1)  # star-graph maximum for [0,1]-scaled scores
    if denominator <= 0.0:
        return 0.0
    return max(0.0, min(1.0, numerator / denominator))


def _fractal_dimension(coordinates: list) -> float:
    """Box-counting dimension of the path, mapped to [0,1] via /2 (plane)."""
    points = _unique_points(coordinates)
    if len(points) < 2:
        return 0.0
    array = np.asarray(points, dtype=float)
    span = float(np.max(np.ptp(array, axis=0)))
    if span <= 0.0:
        return 0.0

    mins = np.min(array, axis=0)
    counts: list[tuple[float, float]] = []
    for divisions in (2, 4, 8):
        box = span / divisions
        if box <= 0.0:
            continue
        occupied = {
            tuple(np.floor((point - mins) / box).astype(int))
            for point in array
        }
        counts.append((np.log(1.0 / box), np.log(len(occupied))))
    if len(counts) < 2:
        return 0.0
    xs = np.array([c[0] for c in counts])
    ys = np.array([c[1] for c in counts])
    slope = float(np.polyfit(xs, ys, 1)[0])
    return max(0.0, min(1.0, slope / 2.0))


def _unique_points(coordinates: list) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    seen: set[tuple[float, float]] = set()
    for coordinate in coordinates:
        if not isinstance(coordinate, (list, tuple)) or len(coordinate) < 2:
            continue
        point = (float(coordinate[0]), float(coordinate[1]))
        if point not in seen:
            seen.add(point)
            points.append(point)
    return points
