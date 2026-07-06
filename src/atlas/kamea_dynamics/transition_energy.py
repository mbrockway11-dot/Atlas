
"""Kamea transition energy metrics."""

from __future__ import annotations

import math
from typing import Any


def analyze_transition_energy(stream: dict[str, Any]) -> dict[str, Any]:
    """Analyze transition distance and effort across a stream."""
    trajectory = stream.get("trajectory", []) or []
    energies = []

    for left, right in zip(trajectory, trajectory[1:]):
        dx = float(right.get("x") or 0.0) - float(left.get("x") or 0.0)
        dy = float(right.get("y") or 0.0) - float(left.get("y") or 0.0)
        distance = math.sqrt(dx * dx + dy * dy)
        depth_change = int(right.get("visit_depth") or 0) - int(left.get("visit_depth") or 0)

        energies.append(
            {
                "source": left.get("node"),
                "target": right.get("node"),
                "distance": round(distance, 6),
                "depth_change": depth_change,
                "energy": round(distance * (1.0 + max(0, depth_change) * 0.25), 6),
            }
        )

    total_energy = sum(row["energy"] for row in energies)

    return {
        "stream_id": stream.get("stream_id"),
        "transition_count": len(energies),
        "total_energy": round(total_energy, 6),
        "mean_energy": round(total_energy / max(1, len(energies)), 6),
        "max_energy": max([row["energy"] for row in energies] or [0.0]),
        "transitions": energies,
    }
