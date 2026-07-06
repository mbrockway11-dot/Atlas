
"""Kamea attractor detection."""

from __future__ import annotations

from collections import Counter
from typing import Any


def detect_attractors(stream: dict[str, Any]) -> dict[str, Any]:
    """Detect node and edge attractors in one stream."""
    trajectory = stream.get("trajectory", []) or []
    node_counts = Counter(row.get("node") for row in trajectory)

    edge_counts = Counter()
    for left, right in zip(trajectory, trajectory[1:]):
        edge_counts[f"{left.get('node')}->{right.get('node')}"] += 1

    node_attractors = [
        {
            "node": node,
            "visits": count,
            "strength": round(count / max(1, len(trajectory)), 6),
        }
        for node, count in node_counts.most_common()
        if count > 1
    ]

    edge_attractors = [
        {
            "edge": edge,
            "visits": count,
            "strength": round(count / max(1, max(1, len(trajectory) - 1)), 6),
        }
        for edge, count in edge_counts.most_common()
        if count > 1
    ]

    return {
        "stream_id": stream.get("stream_id"),
        "node_attractor_count": len(node_attractors),
        "edge_attractor_count": len(edge_attractors),
        "node_attractors": node_attractors,
        "edge_attractors": edge_attractors,
        "dominant_attractor": node_attractors[0] if node_attractors else None,
    }
