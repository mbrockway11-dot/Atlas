
"""Structural tensions section."""

from __future__ import annotations

from typing import Any


TENSION_EXPLANATIONS = {
    ("persistent_architecture", "innovation_pattern"): "The system favors continuity but also contains novelty pressure. Innovation may emerge after enough structure is established.",
    ("constraint_pattern", "activation_driven_action"): "The system may alternate between compression and action. Execution improves when pressure is structured rather than impulsive.",
    ("stability_seeking", "activation_driven_action"): "The system balances calm regulation against activation surges.",
    ("structural_selectivity", "signal_amplification"): "The system may filter heavily before broadcasting signals outward.",
}


def build_tensions_section(payload: dict[str, Any]) -> dict[str, Any]:
    """Build structural tensions section."""
    conflicts = payload.get("synthesis", {}).get("inference_graph", {}).get("conflicts", [])

    rows = []
    for pair in conflicts:
        left, right = pair[0], pair[1]
        explanation = (
            TENSION_EXPLANATIONS.get((left, right))
            or TENSION_EXPLANATIONS.get((right, left))
            or "This pair indicates competing structural tendencies."
        )
        rows.append({"left": left, "right": right, "explanation": explanation})

    return {
        "tension_count": len(rows),
        "tensions": rows,
    }
