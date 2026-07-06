
"""Evolution architecture section."""

from __future__ import annotations

from typing import Any


def build_evolution_section(payload: dict[str, Any]) -> dict[str, Any]:
    """Build evolution/state-transition section."""
    reasoning = payload.get("synthesis", {}).get("reasoning", {}).get("strongest_inferences", [])

    return {
        "state_model": [
            "Stable architecture",
            "Pressure point",
            "Adaptive response",
            "Reintegrated structure",
        ],
        "growth_related_inferences": [
            item for item in reasoning
            if item.get("category") == "growth_path"
        ],
    }
