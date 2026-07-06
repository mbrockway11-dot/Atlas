
"""Dynamic profile signature."""

from __future__ import annotations

from typing import Any


def build_profile_dynamic_signature(signature: dict[str, Any]) -> dict[str, Any]:
    """Build normalized profile dynamic signature."""
    metrics = signature.get("dynamic_metrics", {}) or {}

    recurrence = float(metrics.get("mean_recurrence") or 0.0)
    energy = float(metrics.get("mean_energy") or 0.0)
    attractors = float(metrics.get("attractor_count") or 0.0)
    streams = float(metrics.get("stream_count") or 1.0)

    attractor_density = attractors / max(1.0, streams)

    return {
        "profile_key": signature.get("profile_key"),
        "flow_stability": classify_flow_stability(recurrence, attractor_density),
        "recurrence": round(recurrence, 6),
        "mean_energy": round(energy, 6),
        "attractor_density": round(attractor_density, 6),
        "field_node_count": metrics.get("field_node_count", 0),
        "field_edge_count": metrics.get("field_edge_count", 0),
        "phase_complexity": classify_phase_complexity(metrics),
    }


def classify_flow_stability(recurrence: float, attractor_density: float) -> str:
    """Classify flow stability."""
    if recurrence >= 0.45 and attractor_density >= 3.0:
        return "high_recurrence_stable_basin"

    if recurrence >= 0.25:
        return "moderate_recurrence_field"

    if recurrence <= 0.10:
        return "low_recurrence_diffuse_flow"

    return "mixed_dynamic_field"


def classify_phase_complexity(metrics: dict[str, Any]) -> str:
    """Classify phase complexity."""
    nodes = int(metrics.get("field_node_count") or 0)
    edges = int(metrics.get("field_edge_count") or 0)

    ratio = edges / max(1, nodes)

    if ratio >= 5.0:
        return "high_current_density"

    if ratio >= 3.0:
        return "moderate_current_density"

    return "low_current_density"
