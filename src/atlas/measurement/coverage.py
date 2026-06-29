"""Coverage measurements."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


Coordinate = tuple[int, int]
Edge = tuple[Coordinate, Coordinate]


@dataclass(frozen=True)
class CoverageMeasurement:
    """How much of the Kamea measurement space is explored."""

    node_coverage: float
    edge_coverage: float
    axis_coverage: float
    boundary_coverage: float
    core_coverage: float


def measure_coverage(
    nodes: Counter[Coordinate],
    edges: Counter[Edge],
    grid_size: int,
) -> CoverageMeasurement:
    """Measure coverage for one oriented path."""
    grid_capacity = grid_size * grid_size
    possible_edges = grid_capacity * max(grid_capacity - 1, 1)

    return CoverageMeasurement(
        node_coverage=safe_ratio(len(nodes), grid_capacity),
        edge_coverage=safe_ratio(len(edges), possible_edges),
        axis_coverage=axis_coverage(nodes, grid_size),
        boundary_coverage=boundary_coverage(nodes, grid_size),
        core_coverage=core_coverage(nodes, grid_size),
    )


def axis_coverage(
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


def boundary_coverage(
    nodes: Counter[Coordinate],
    grid_size: int,
) -> float:
    """Ratio of visited nodes on the outer boundary."""
    if not nodes:
        return 0.0

    boundary_nodes = [
        node
        for node in nodes
        if (
            node[0] == 0
            or node[1] == 0
            or node[0] == grid_size - 1
            or node[1] == grid_size - 1
        )
    ]

    return safe_ratio(len(boundary_nodes), len(nodes))


def core_coverage(
    nodes: Counter[Coordinate],
    grid_size: int,
) -> float:
    """Ratio of visited nodes in the non-boundary core."""
    if not nodes:
        return 0.0

    core_nodes = [
        node
        for node in nodes
        if (
            node[0] != 0
            and node[1] != 0
            and node[0] != grid_size - 1
            and node[1] != grid_size - 1
        )
    ]

    return safe_ratio(len(core_nodes), len(nodes))


def safe_ratio(numerator: float, denominator: float) -> float:
    """Safely divide and clamp to 0-1."""
    if denominator == 0:
        return 0.0

    return clamp(float(numerator) / float(denominator))


def clamp(value: float) -> float:
    """Clamp value to 0-1."""
    return max(0.0, min(1.0, value))