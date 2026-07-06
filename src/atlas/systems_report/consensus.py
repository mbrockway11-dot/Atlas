
"""Systems report consensus section."""

from __future__ import annotations

from typing import Any


def build_consensus_section(payload: dict[str, Any]) -> dict[str, Any]:
    """Build consensus section."""
    consensus = payload.get("synthesis", {}).get("consensus", {})

    return {
        "dominant_themes": consensus.get("dominant_themes", []),
        "strong_themes": consensus.get("strong_themes", []),
        "moderate_themes": consensus.get("moderate_themes", []),
        "weak_themes": consensus.get("weak_themes", []),
        "category_summary": consensus.get("category_summary", {}),
    }
