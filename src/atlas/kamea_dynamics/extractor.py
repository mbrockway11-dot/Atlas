
"""Extract Kamea dynamics trajectories from canonical Kamea payload."""

from __future__ import annotations

from typing import Any


def extract_dynamics_streams(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract 21 cipher/planet trajectory streams from canonical Kamea."""
    kamea = payload.get("kamea", {}) or {}
    passes = kamea.get("construction_passes", []) or []

    streams = []

    for item in passes:
        cipher = str(item.get("cipher") or "unknown_cipher")
        planet = str(item.get("planet") or "unknown_planet")
        analysis = ((item.get("path_views") or {}).get("analysis_path") or {})
        visit_history = analysis.get("visit_history", {}) or {}
        visits = visit_history.get("visits", []) or []

        trajectory = []

        for visit in visits:
            coord = visit.get("coordinate") or [0, 0]
            trajectory.append(
                {
                    "node": str(visit.get("node")),
                    "x": float(coord[0]) if len(coord) > 0 else 0.0,
                    "y": float(coord[1]) if len(coord) > 1 else 0.0,
                    "sequence_index": int(visit.get("sequence_index") or 0),
                    "visit_depth": int(visit.get("visit_depth") or 0),
                }
            )

        streams.append(
            {
                "stream_id": f"{cipher}::{planet}",
                "cipher": cipher,
                "planet": planet,
                "trajectory": sorted(trajectory, key=lambda row: row["sequence_index"]),
                "node_weights": analysis.get("node_weights", {}),
                "edge_weights": analysis.get("edge_weights", {}),
                "coordinate_edge_weights": analysis.get("coordinate_edge_weights", []),
                "raw_values": analysis.get("raw_values", []),
                "wrapped_values": analysis.get("wrapped_values", []),
                "coordinates": analysis.get("coordinates", []),
                "max_depth": int(visit_history.get("max_depth") or 0),
            }
        )

    return streams
