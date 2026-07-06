
"""Career architecture interpretation."""

from __future__ import annotations

from typing import Any


def build_career_architecture(payload: dict[str, Any]) -> dict[str, Any]:
    """Build deterministic career architecture interpretation."""
    systems = payload.get("systems_report", {}) or {}
    executive = systems.get("executive", {}) or {}

    system_class = executive.get("system_class", "unresolved")
    primary = executive.get("primary_architecture", "unresolved")
    themes = executive.get("strongest_themes", []) or []

    strengths = []
    environments = []

    if "persistent_architecture" in themes:
        strengths.append("long-horizon system building")
        environments.append("work requiring durable structure and continuity")

    if "information_routing" in themes:
        strengths.append("cross-domain translation")
        environments.append("roles involving synthesis, coordination, or architecture")

    if "visible_authorship" in themes:
        strengths.append("expressive leadership through authored structure")
        environments.append("contexts where original frameworks can be made visible")

    if not strengths:
        strengths.append("career architecture is not yet strongly resolved")

    return {
        "success": True,
        "domain": "career_architecture",
        "system_class": system_class,
        "primary_architecture": primary,
        "strengths": strengths,
        "best_environments": environments,
        "summary": "Career architecture describes where the profile is most likely to create durable contribution.",
    }
