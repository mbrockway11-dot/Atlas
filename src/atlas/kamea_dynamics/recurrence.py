
"""Kamea recurrence metrics."""

from __future__ import annotations

from collections import Counter
from typing import Any


def analyze_recurrence(stream: dict[str, Any]) -> dict[str, Any]:
    """Analyze recurrence in one stream."""
    trajectory = stream.get("trajectory", []) or []
    counts = Counter(row.get("node") for row in trajectory)

    revisits = [
        row for row in trajectory
        if int(row.get("visit_depth") or 0) > 0
    ]

    repeated_nodes = [
        {"node": node, "visits": count}
        for node, count in counts.most_common()
        if count > 1
    ]

    return {
        "stream_id": stream.get("stream_id"),
        "step_count": len(trajectory),
        "unique_node_count": len(counts),
        "revisit_count": len(revisits),
        "recurrence_ratio": round(len(revisits) / max(1, len(trajectory)), 6),
        "max_visit_depth": max([int(row.get("visit_depth") or 0) for row in trajectory] or [0]),
        "repeated_nodes": repeated_nodes,
        "first_revisit_index": first_revisit_index(trajectory),
    }


def first_revisit_index(trajectory: list[dict[str, Any]]) -> int | None:
    """Return first sequence index where revisit occurs."""
    for row in trajectory:
        if int(row.get("visit_depth") or 0) > 0:
            return int(row.get("sequence_index") or 0)
    return None
