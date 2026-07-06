
"""Growth modeling."""

from __future__ import annotations

from typing import Any


def build_growth_model(simulation: dict[str, Any]) -> dict[str, Any]:
    """Build growth model from simulation output."""
    decisions = simulation.get("decisions", {})
    likely = decisions.get("likely_action") or {}

    return {
        "current_growth_vector": likely.get("action", "unresolved"),
        "growth_sequence": [
            "recognize active state",
            "choose stabilizing behavior",
            "convert pressure into structure",
            "create reusable artifact",
        ],
        "measurement": "growth is modeled as improved recovery speed and cleaner transition back to stable architecture",
    }
