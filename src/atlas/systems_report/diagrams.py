
"""Systems report diagram specs."""

from __future__ import annotations

from typing import Any


def build_diagrams_section(payload: dict[str, Any]) -> dict[str, Any]:
    """Build lightweight diagram specs."""
    inference_graph = payload.get("synthesis", {}).get("inference_graph", {})

    return {
        "pipeline": [
            "Identity",
            "Evidence",
            "Fusion",
            "Consensus",
            "Reasoning",
            "Inference Graph",
            "Systems Report",
        ],
        "inference_graph": inference_graph,
    }
