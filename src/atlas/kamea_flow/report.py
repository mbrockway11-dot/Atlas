
"""Kamea Flow report builder."""

from __future__ import annotations

from typing import Any

from atlas.kamea_flow.flow import build_kamea_flow
from atlas.kamea_flow.metrics import build_kamea_flow_metrics
from atlas.kamea_flow.riverbed import build_invariant_riverbed
from atlas.kamea_flow.shape import build_unified_shape_analysis
from atlas.kamea_flow.tributaries import build_kamea_tributaries


KAMEA_FLOW_REPORT_VERSION = "2.0.0"


def build_kamea_flow_report(payload: dict[str, Any]) -> dict[str, Any]:
    """Build full Kamea Flow report."""
    flow = build_kamea_flow(payload)
    metrics = build_kamea_flow_metrics(flow)
    tributaries = build_kamea_tributaries(flow)
    riverbed = build_invariant_riverbed(flow)
    shape = build_unified_shape_analysis(flow)

    return {
        "success": True,
        "version": KAMEA_FLOW_REPORT_VERSION,
        "profile_key": payload.get("profile_key"),
        "flow": flow,
        "metrics": metrics,
        "tributaries": tributaries,
        "riverbed": riverbed,
        "shape": shape,
        "interpretive_model": {
            "name": "Kamea consciousness-flow metaphor",
            "source": "encoded identity sequence",
            "filter": "planetary Kamea coordinate field",
            "current": "ordered full traversal",
            "tributary": "one cipher-planet stream",
            "pool_or_attractor": "revisited node or shared same-planet node",
            "riverbed": "node or directed channel reproduced across cipher streams",
            "claim_type": "symbolic_interpretation",
            "empirical_consciousness_measurement": False,
            "causal_claim": False,
        },
        "summary": build_summary(flow, metrics, tributaries),
    }


def build_summary(flow: dict[str, Any], metrics: dict[str, Any], tributaries: dict[str, Any] | None = None) -> str:
    """Build human-readable Kamea Flow summary."""
    m = metrics.get("metrics", {}) or {}
    s = flow.get("summary", {}) or {}

    t = tributaries.get("summary", {}) if tributaries else {}

    return (
        f"Kamea Flow models the reduced Kamea path as ordered movement through a symbolic field. "
        f"This profile produced {flow.get('step_count', 0)} flow step(s), "
        f"{flow.get('edge_count', 0)} directed transition(s), and "
        f"{tributaries.get('tributary_count', 0) if tributaries else 0} tributary stream(s). "
        f"Global entropy is {m.get('flow_entropy', 0.0)}, recurrence is {m.get('recurrence_ratio', 0.0)}, "
        f"and directional coherence is {m.get('directional_coherence', 0.0)}. "
        f"Tributary mean recurrence is {t.get('mean_recurrence', 0.0)} and mean directional coherence is "
        f"{t.get('mean_directional_coherence', 0.0)}."
    )
