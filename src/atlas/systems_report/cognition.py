
"""Cognitive architecture section."""

from __future__ import annotations

from typing import Any


COGNITIVE_FEATURES = {
    "distributed_integration",
    "information_routing",
    "complexity_tolerance",
    "cross_domain_linking",
    "parallel_context_management",
    "pattern_compression",
    "high_resolution_discrimination",
}


def build_cognition_section(payload: dict[str, Any]) -> dict[str, Any]:
    """Build cognitive architecture section."""
    themes = payload.get("synthesis", {}).get("fusion", {}).get("themes", [])

    selected = [
        theme for theme in themes
        if theme.get("feature") in COGNITIVE_FEATURES
        or theme.get("category") == "cognitive_architecture"
    ]

    return {
        "flow": [
            "Input",
            "Pattern detection",
            "Cross-domain routing",
            "Structural compression",
            "Internal validation",
            "Output",
        ],
        "themes": selected,
    }
