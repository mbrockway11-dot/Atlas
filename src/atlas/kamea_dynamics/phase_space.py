
"""Kamea phase-space representation."""

from __future__ import annotations

from typing import Any


def build_phase_space(stream: dict[str, Any]) -> dict[str, Any]:
    """Build 3D phase-space points using x, y, visit_depth."""
    points = []

    for row in stream.get("trajectory", []) or []:
        points.append(
            {
                "t": row.get("sequence_index"),
                "node": row.get("node"),
                "x": row.get("x"),
                "y": row.get("y"),
                "z": row.get("visit_depth"),
            }
        )

    return {
        "stream_id": stream.get("stream_id"),
        "point_count": len(points),
        "points": points,
        "max_depth": max([int(point.get("z") or 0) for point in points] or [0]),
    }
