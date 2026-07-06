
"""Decision scoring for structural alignment."""

from __future__ import annotations

from typing import Any


POSITIVE_ACTIONS = {
    "structure_plan",
    "sequence_work",
    "protect_continuity",
    "map_relationships",
    "connect_domains",
    "compress_into_model",
    "build_symbolic_artifact",
    "explain_publicly",
    "teach_framework",
    "publish_artifact",
}

STRESS_ACTIONS = {
    "reduce_noise",
    "stabilize_environment",
    "execute_conservatively",
}


def score_decision_path(simulation: dict[str, Any]) -> dict[str, Any]:
    """Score a simulated decision path."""
    sim = simulation.get("simulation", {})
    decisions = sim.get("decisions", {})
    likely = decisions.get("likely_action") or {}
    action = likely.get("action", "unresolved")
    action_score = float(likely.get("score") or 0.0)

    propagation = sim.get("propagation", {})
    top_nodes = propagation.get("top_activated", [])

    recovery = sim.get("recovery", {})
    growth = simulation.get("growth", {})

    alignment = structural_alignment(action, action_score, top_nodes)
    growth_score = growth_alignment(growth, top_nodes)
    stress_score = stress_load(action, top_nodes)
    recovery_score = recovery_alignment(recovery)

    total = (
        alignment * 0.35
        + growth_score * 0.25
        + recovery_score * 0.25
        + (1.0 - stress_score) * 0.15
    )

    return {
        "action": action,
        "action_score": round(action_score, 6),
        "structural_alignment": round(alignment, 6),
        "growth_alignment": round(growth_score, 6),
        "recovery_alignment": round(recovery_score, 6),
        "stress_load": round(stress_score, 6),
        "overall_score": round(total, 6),
        "label": score_label(total),
    }


def structural_alignment(action: str, action_score: float, top_nodes: list[dict[str, Any]]) -> float:
    """Score structural alignment."""
    score = max(0.35, action_score * 0.65) if action != "unresolved" else 0.15

    if action in POSITIVE_ACTIONS:
        score += 0.20

    active_names = {
        str(item.get("node_id", "")).replace("theme:", "").replace("inference:", "")
        for item in top_nodes
    }

    if "compound_systems_builder" in active_names:
        score += 0.08

    if "cross_domain_synthesizer" in active_names:
        score += 0.06

    if "visible_structural_author" in active_names:
        score += 0.05

    return min(1.0, score)


def growth_alignment(growth: dict[str, Any], top_nodes: list[dict[str, Any]]) -> float:
    """Score growth alignment."""
    vector = growth.get("current_growth_vector", "")
    score = 0.50

    if vector in POSITIVE_ACTIONS:
        score += 0.25

    if top_nodes:
        score += min(0.20, len(top_nodes) * 0.02)

    return min(1.0, score)


def recovery_alignment(recovery: dict[str, Any]) -> float:
    """Score recovery quality."""
    mode = str(recovery.get("recovery_mode", ""))
    path = recovery.get("recovery_path", [])

    score = 0.45 + min(0.25, len(path) * 0.05)

    if "stable" in mode or "coherence" in mode or "structure" in mode:
        score += 0.20

    return min(1.0, score)


def stress_load(action: str, top_nodes: list[dict[str, Any]]) -> float:
    """Score stress load."""
    score = 0.25

    if action in STRESS_ACTIONS:
        score += 0.20

    for item in top_nodes:
        node_id = str(item.get("node_id", ""))
        activation = float(item.get("activation") or 0.0)

        if "tension" in node_id or "innovation_pressure" in node_id:
            score += activation * 0.15

        if "constraint_pattern" in node_id:
            score += activation * 0.08

    return min(1.0, score)


def score_label(score: float) -> str:
    """Return decision score label."""
    if score >= 0.82:
        return "high_structural_alignment"

    if score >= 0.68:
        return "moderate_structural_alignment"

    if score >= 0.52:
        return "mixed_alignment"

    return "low_alignment"
