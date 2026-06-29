"""Structural stability measurements."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

Coordinate = tuple[int, int]
Edge = tuple[Coordinate, Coordinate]


@dataclass(frozen=True)
class StabilityMeasurement:
    """Persistence and stability metrics."""

    repeat_node_ratio: float
    repeat_edge_ratio: float
    self_loop_ratio: float
    hub_persistence: float
    bridge_persistence: float


def measure_stability(
    nodes: Counter[Coordinate],
    edges: Counter[Edge],
) -> StabilityMeasurement:
    """Measure structural persistence."""

    total_node_visits = sum(nodes.values())
    total_edge_visits = sum(edges.values())

    repeated_nodes = sum(
        1
        for count in nodes.values()
        if count > 1
    )

    repeated_edges = sum(
        1
        for count in edges.values()
        if count > 1
    )

    self_loops = sum(
        count
        for (source, target), count in edges.items()
        if source == target
    )

    hub = max(nodes.values(), default=0)
    bridge = max(edges.values(), default=0)

    return StabilityMeasurement(
        repeat_node_ratio=safe_ratio(
            repeated_nodes,
            len(nodes),
        ),
        repeat_edge_ratio=safe_ratio(
            repeated_edges,
            len(edges),
        ),
        self_loop_ratio=safe_ratio(
            self_loops,
            total_edge_visits,
        ),
        hub_persistence=safe_ratio(
            hub,
            total_node_visits,
        ),
        bridge_persistence=safe_ratio(
            bridge,
            total_edge_visits,
        ),
    )


def safe_ratio(a: float, b: float) -> float:
    if b == 0:
        return 0.0

    return max(
        0.0,
        min(
            1.0,
            float(a) / float(b),
        ),
    )