
"""Behavioral dynamics section."""

from __future__ import annotations

from typing import Any


BEHAVIOR_FEATURES = {
    "long_horizon_planning",
    "durable_system_construction",
    "continuity_preservation",
    "stability_seeking",
    "constraint_sensitive_execution",
    "activation_driven_action",
    "iterative_refinement",
}


def build_behavior_section(payload: dict[str, Any]) -> dict[str, Any]:
    """Build behavioral dynamics section."""
    themes = payload.get("synthesis", {}).get("fusion", {}).get("themes", [])

    selected = [
        theme for theme in themes
        if theme.get("feature") in BEHAVIOR_FEATURES
    ]

    return {
        "decision_style": infer_decision_style(selected),
        "themes": selected,
    }


def infer_decision_style(themes: list[dict[str, Any]]) -> str:
    """Infer simple decision style."""
    features = {theme.get("feature") for theme in themes}

    if "constraint_sensitive_execution" in features:
        return "constraint-first"
    if "long_horizon_planning" in features:
        return "long-horizon"
    if "activation_driven_action" in features:
        return "activation-driven"

    return "mixed"
