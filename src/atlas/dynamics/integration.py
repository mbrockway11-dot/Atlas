
"""Integrate Systems Report with Kamea Dynamics."""

from __future__ import annotations

from typing import Any

from atlas.kamea_dynamics import build_kamea_dynamics_report


def build_dynamic_signature(payload: dict[str, Any]) -> dict[str, Any]:
    """Build unified dynamic signature from canonical payload."""
    systems = payload.get("systems_report", {}) or {}
    dynamics = build_kamea_dynamics_report(payload)

    return {
        "profile_key": payload.get("profile_key"),
        "systems_summary": systems.get("executive", {}) or systems.get("executive_summary", {}),
        "strongest_themes": extract_strongest_themes(systems),
        "dynamic_metrics": extract_dynamic_metrics(dynamics),
        "dynamic_field": dynamics.get("flow_field", {}),
        "kamea_dynamics": dynamics,
    }


def extract_strongest_themes(systems: dict[str, Any]) -> list[str]:
    """Extract strongest systems themes."""
    executive = systems.get("executive", {}) or systems.get("executive_summary", {})
    return list(executive.get("strongest_themes", []) or [])


def extract_dynamic_metrics(dynamics: dict[str, Any]) -> dict[str, Any]:
    """Extract compact Kamea Dynamics metrics."""
    streams = dynamics.get("streams", []) or []

    if not streams:
        return {
            "stream_count": 0,
            "mean_recurrence": 0.0,
            "mean_energy": 0.0,
            "attractor_count": 0,
            "field_node_count": 0,
            "field_edge_count": 0,
        }

    recurrence_values = [
        float(item.get("recurrence", {}).get("recurrence_ratio") or 0.0)
        for item in streams
    ]

    energy_values = [
        float(item.get("transition_energy", {}).get("mean_energy") or 0.0)
        for item in streams
    ]

    attractor_count = sum(
        int(item.get("attractors", {}).get("node_attractor_count") or 0)
        for item in streams
    )

    field = dynamics.get("flow_field", {}) or {}

    return {
        "stream_count": len(streams),
        "mean_recurrence": round(sum(recurrence_values) / len(recurrence_values), 6),
        "mean_energy": round(sum(energy_values) / len(energy_values), 6),
        "attractor_count": attractor_count,
        "field_node_count": int(field.get("node_count") or 0),
        "field_edge_count": int(field.get("edge_count") or 0),
    }
