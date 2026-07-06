
"""Kamea Flow metrics."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any


def build_kamea_flow_metrics(flow: dict[str, Any]) -> dict[str, Any]:
    """Build dynamic metrics for a Kamea flow."""
    steps = flow.get("steps", []) or []
    edges = flow.get("edges", []) or []

    return {
        "success": True,
        "profile_key": flow.get("profile_key"),
        "metrics": {
            "flow_entropy": flow_entropy(steps),
            "recurrence_ratio": recurrence_ratio(steps),
            "directional_coherence": directional_coherence(edges),
            "path_efficiency": path_efficiency(steps, edges),
            "edge_reuse_ratio": edge_reuse_ratio(edges),
            "planetary_flow_balance": category_balance(steps, "planet"),
            "cipher_flow_balance": category_balance(steps, "cipher"),
        },
    }


def flow_entropy(steps: list[dict[str, Any]]) -> float:
    """Measure node visitation entropy."""
    counts = Counter(str(step.get("node")) for step in steps)
    total = sum(counts.values())

    if total == 0:
        return 0.0

    entropy = 0.0

    for count in counts.values():
        probability = count / total
        entropy -= probability * math.log(probability, 2)

    max_entropy = math.log(max(1, len(counts)), 2)

    if max_entropy == 0.0:
        return 0.0

    return round(entropy / max_entropy, 6)


def recurrence_ratio(steps: list[dict[str, Any]]) -> float:
    """Measure how often the path revisits nodes."""
    if not steps:
        return 0.0

    unique = len({str(step.get("node")) for step in steps})
    total = len(steps)

    return round(1.0 - (unique / total), 6)


def directional_coherence(edges: list[dict[str, Any]]) -> float:
    """Measure alignment of edge directions."""
    if not edges:
        return 0.0

    total_weight = 0.0
    vector_x = 0.0
    vector_y = 0.0

    for edge in edges:
        weight = float(edge.get("count") or 1.0)
        dx = float(edge.get("direction_x") or 0.0)
        dy = float(edge.get("direction_y") or 0.0)
        distance = math.sqrt(dx * dx + dy * dy)

        if distance == 0.0:
            continue

        vector_x += (dx / distance) * weight
        vector_y += (dy / distance) * weight
        total_weight += weight

    if total_weight == 0.0:
        return 0.0

    magnitude = math.sqrt(vector_x * vector_x + vector_y * vector_y)

    return round(min(1.0, magnitude / total_weight), 6)


def path_efficiency(
    steps: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> float:
    """Measure direct displacement versus traveled distance."""
    if len(steps) < 2:
        return 0.0

    start = steps[0]
    end = steps[-1]

    dx = float(end.get("x") or 0.0) - float(start.get("x") or 0.0)
    dy = float(end.get("y") or 0.0) - float(start.get("y") or 0.0)

    displacement = math.sqrt(dx * dx + dy * dy)
    traveled = sum(float(edge.get("distance") or 0.0) * float(edge.get("count") or 1.0) for edge in edges)

    if traveled == 0.0:
        return 0.0

    return round(min(1.0, displacement / traveled), 6)


def edge_reuse_ratio(edges: list[dict[str, Any]]) -> float:
    """Measure how much directed transitions repeat."""
    if not edges:
        return 0.0

    total = sum(int(edge.get("count") or 0) for edge in edges)
    unique = len(edges)

    if total == 0:
        return 0.0

    return round(1.0 - (unique / total), 6)


def category_balance(steps: list[dict[str, Any]], key: str) -> float:
    """Measure balance across a categorical field."""
    counts = Counter(str(step.get(key) or "unknown") for step in steps)
    total = sum(counts.values())

    if total == 0 or len(counts) <= 1:
        return 0.0

    entropy = 0.0

    for count in counts.values():
        probability = count / total
        entropy -= probability * math.log(probability, 2)

    max_entropy = math.log(len(counts), 2)

    return round(entropy / max_entropy, 6)
