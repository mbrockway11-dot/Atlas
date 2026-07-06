
"""Kamea Flow report builder."""

from __future__ import annotations

from typing import Any

from atlas.kamea_flow.flow import build_kamea_flow
from atlas.kamea_flow.metrics import build_kamea_flow_metrics


KAMEA_FLOW_REPORT_VERSION = "1.0.0"


def build_kamea_flow_report(payload: dict[str, Any]) -> dict[str, Any]:
    """Build full Kamea Flow report."""
    flow = build_kamea_flow(payload)
    metrics = build_kamea_flow_metrics(flow)

    return {
        "success": True,
        "version": KAMEA_FLOW_REPORT_VERSION,
        "profile_key": payload.get("profile_key"),
        "flow": flow,
        "metrics": metrics,
        "summary": build_summary(flow, metrics),
    }


def build_summary(flow: dict[str, Any], metrics: dict[str, Any]) -> str:
    """Build human-readable Kamea Flow summary."""
    m = metrics.get("metrics", {}) or {}
    s = flow.get("summary", {}) or {}

    return (
        f"Kamea Flow models the reduced Kamea path as ordered movement through a symbolic field. "
        f"This profile produced {flow.get('step_count', 0)} flow step(s), "
        f"{flow.get('edge_count', 0)} directed transition(s), and "
        f"{s.get('repeated_node_count', 0)} repeated node pattern(s). "
        f"Flow entropy is {m.get('flow_entropy', 0.0)}, recurrence is {m.get('recurrence_ratio', 0.0)}, "
        f"and directional coherence is {m.get('directional_coherence', 0.0)}."
    )
