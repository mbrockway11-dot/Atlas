"""Organization measurements."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import log2


Coordinate = tuple[int, int]
Edge = tuple[Coordinate, Coordinate]


@dataclass(frozen=True)
class OrganizationMeasurement:
    """How organized the path topology is."""

    density: float
    clusters: int
    entropy: float
    axis_strength: float
    reciprocity: float
    compression_ratio: float


def measure_organization(
    nodes: Counter[Coordinate],
    edges: Counter[Edge],
    grid_size: int,
) -> OrganizationMeasurement:
    """Measure organization for one oriented path."""
    return OrganizationMeasurement(
        density=density(nodes, edges),
        clusters=cluster_count(nodes, edges),
        entropy=entropy(list(nodes.values())),
        axis_strength=axis_strength(nodes, grid_size),
        reciprocity=reciprocity(edges),
        compression_ratio=compression_ratio(nodes, grid_size),
    )


def density(
    nodes: Counter[Coordinate],
    edges: Counter[Edge],
) -> float:
    """Calculate directed graph density."""
    node_count = len(nodes)

    if node_count <= 1:
        return 0.0

    possible_edges = node_count * (node_count - 1)
    non_loop_edges = sum(
        1
        for source, target in edges
        if source != target
    )

    return safe_ratio(non_loop_edges, possible_edges)


def cluster_count(
    nodes: Counter[Coordinate],
    edges: Counter[Edge],
) -> int:
    """Count weakly connected components."""
    if not nodes:
        return 0

    adjacency: dict[Coordinate, set[Coordinate]] = {
        node: set()
        for node in nodes
    }

    for source, target in edges:
        adjacency.setdefault(source, set()).add(target)
        adjacency.setdefault(target, set()).add(source)

    visited = set()
    clusters = 0

    for node in adjacency:
        if node in visited:
            continue

        clusters += 1
        stack = [node]

        while stack:
            current = stack.pop()

            if current in visited:
                continue

            visited.add(current)
            stack.extend(adjacency[current] - visited)

    return clusters


def entropy(weights: list[int]) -> float:
    """Calculate normalized Shannon entropy."""
    if not weights:
        return 0.0

    total = sum(weights)

    if total == 0:
        return 0.0

    probabilities = [
        weight / total
        for weight in weights
        if weight > 0
    ]

    raw_entropy = -sum(
        probability * log2(probability)
        for probability in probabilities
    )

    max_entropy = log2(len(probabilities)) if len(probabilities) > 1 else 1.0

    if max_entropy == 0:
        return 0.0

    return clamp(raw_entropy / max_entropy)


def axis_strength(
    nodes: Counter[Coordinate],
    grid_size: int,
) -> float:
    """Measure concentration along central row/column/diagonals."""
    if not nodes:
        return 0.0

    total = sum(nodes.values())
    center = (grid_size - 1) / 2

    axis_weight = 0.0

    for (row, col), weight in nodes.items():
        on_middle_row = row == center
        on_middle_col = col == center
        on_main_diag = row == col
        on_anti_diag = row + col == grid_size - 1

        if on_middle_row or on_middle_col or on_main_diag or on_anti_diag:
            axis_weight += weight

    return safe_ratio(axis_weight, total)


def reciprocity(edges: Counter[Edge]) -> float:
    """Ratio of edges that have a reverse counterpart."""
    if not edges:
        return 0.0

    reciprocal_count = 0

    for source, target in edges:
        if (target, source) in edges:
            reciprocal_count += 1

    return safe_ratio(reciprocal_count, len(edges))


def compression_ratio(
    nodes: Counter[Coordinate],
    grid_size: int,
) -> float:
    """Ratio of path activity compressed into active nodes."""
    grid_capacity = grid_size * grid_size

    if grid_capacity == 0:
        return 0.0

    return clamp(1.0 - (len(nodes) / grid_capacity))


def safe_ratio(numerator: float, denominator: float) -> float:
    """Safely divide and clamp to 0-1."""
    if denominator == 0:
        return 0.0

    return clamp(float(numerator) / float(denominator))


def clamp(value: float) -> float:
    """Clamp value to 0-1."""
    return max(0.0, min(1.0, value))