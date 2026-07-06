
"""Kamea Dynamics report builder."""

from __future__ import annotations

from typing import Any

from atlas.kamea_dynamics.attractors import detect_attractors
from atlas.kamea_dynamics.extractor import extract_dynamics_streams
from atlas.kamea_dynamics.flow_field import build_flow_field
from atlas.kamea_dynamics.phase_space import build_phase_space
from atlas.kamea_dynamics.recurrence import analyze_recurrence
from atlas.kamea_dynamics.transition_energy import analyze_transition_energy


KAMEA_DYNAMICS_VERSION = "1.0.0"


def build_kamea_dynamics_report(payload: dict[str, Any]) -> dict[str, Any]:
    """Build Kamea Dynamics report from canonical payload."""
    streams = extract_dynamics_streams(payload)

    stream_reports = []

    for stream in streams:
        stream_reports.append(
            {
                "stream_id": stream.get("stream_id"),
                "cipher": stream.get("cipher"),
                "planet": stream.get("planet"),
                "recurrence": analyze_recurrence(stream),
                "attractors": detect_attractors(stream),
                "transition_energy": analyze_transition_energy(stream),
                "phase_space": build_phase_space(stream),
            }
        )

    field = build_flow_field(streams)

    return {
        "success": True,
        "version": KAMEA_DYNAMICS_VERSION,
        "profile_key": payload.get("profile_key"),
        "stream_count": len(streams),
        "streams": stream_reports,
        "flow_field": field,
        "summary": build_summary(stream_reports, field),
    }


def build_summary(streams: list[dict[str, Any]], field: dict[str, Any]) -> str:
    """Build human-readable summary."""
    if not streams:
        return "Kamea Dynamics found no streams."

    mean_recurrence = sum(
        float(item.get("recurrence", {}).get("recurrence_ratio") or 0.0)
        for item in streams
    ) / len(streams)

    total_node_attractors = sum(
        int(item.get("attractors", {}).get("node_attractor_count") or 0)
        for item in streams
    )

    return (
        f"Kamea Dynamics modeled {len(streams)} stream(s) as trajectories through phase space. "
        f"Mean recurrence is {mean_recurrence:.3f}, with {total_node_attractors} node attractor pattern(s). "
        f"The shared flow field contains {field.get('node_count', 0)} node(s) and {field.get('edge_count', 0)} directed current(s)."
    )
