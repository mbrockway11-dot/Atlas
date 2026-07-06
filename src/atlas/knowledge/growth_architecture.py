
"""Growth architecture interpretation."""

from __future__ import annotations

from typing import Any


def build_growth_architecture(payload: dict[str, Any]) -> dict[str, Any]:
    """Build deterministic growth architecture interpretation."""
    systems = payload.get("systems_report", {}) or {}
    tensions = systems.get("tensions", {}) or {}
    dynamics = payload.get("dynamics", {}) or {}

    dynamic_profile = dynamics.get("dynamic_profile", {}) or {}
    tension_rows = tensions.get("tensions", []) or []

    growth_path = []

    if tension_rows:
        growth_path.append("resolve structural tensions consciously rather than suppressing them")

    if dynamic_profile.get("flow_stability") == "moderate_recurrence_field":
        growth_path.append("use recurrence as practice, not repetition for its own sake")

    if dynamic_profile.get("phase_complexity") == "moderate_current_density":
        growth_path.append("convert complexity into navigable sequences")

    if not growth_path:
        growth_path.append("increase coherence through repeated feedback cycles")

    return {
        "success": True,
        "domain": "growth_architecture",
        "growth_path": growth_path,
        "summary": "Growth architecture describes how the profile matures through tension, recurrence, and integration.",
    }
