
"""Systems report reasoning section."""

from __future__ import annotations

from typing import Any


def build_reasoning_section(payload: dict[str, Any]) -> dict[str, Any]:
    """Build reasoning section."""
    reasoning = payload.get("synthesis", {}).get("reasoning", {})

    return {
        "inference_count": reasoning.get("inference_count", 0),
        "strongest_inferences": reasoning.get("strongest_inferences", []),
        "inferences": reasoning.get("inferences", []),
    }
