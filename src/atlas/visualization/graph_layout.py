"""Deterministic graph layout utilities for Atlas visualizations."""

from __future__ import annotations

import math
from typing import Any


Position = tuple[float, float]


def circular_layout(graph: dict[str, Any], radius: float = 1.0) -> dict[str, Position]:
    """Return deterministic circular node positions."""
    node_ids = sorted(graph.get("nodes", {}))

    if not node_ids:
        return {}

    positions: dict[str, Position] = {}
    count = len(node_ids)

    for index, node_id in enumerate(node_ids):
        angle = (2.0 * math.pi * index) / count
        positions[node_id] = (
            radius * math.cos(angle),
            radius * math.sin(angle),
        )

    return positions


def layered_layout(graph: dict[str, Any]) -> dict[str, Position]:
    """Return simple deterministic layered positions by node degree."""
    nodes = graph.get("nodes", {})

    if not nodes:
        return {}

    ranked = sorted(
        nodes.items(),
        key=lambda item: (
            item[1].get("degree", 0),
            item[1].get("weight", 0),
            item[0],
        ),
        reverse=True,
    )

    positions: dict[str, Position] = {}
    layer_width = max(1, int(math.sqrt(len(ranked))))

    for index, (node_id, _node) in enumerate(ranked):
        row = index // layer_width
        col = index % layer_width
        positions[node_id] = (float(col), -float(row))

    return positions