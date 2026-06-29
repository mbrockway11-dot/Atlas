"""Structural role explanations."""

from __future__ import annotations


ROLE_EXPLANATIONS = {
    "core": "Durable central structure that remains important through transformation.",
    "hub": "A high-connectivity concentration point through which many transitions pass.",
    "bridge": "A connector role linking otherwise separate topological regions.",
    "attractor": "A repeated return-zone or reinforced convergence point.",
    "gateway": "A first-entry or initiating transition role.",
    "exit": "A terminal or release point in the path structure.",
    "oscillator": "A role defined by alternating back-and-forth movement.",
    "loop_anchor": "A stable self-returning or recursive anchor.",
    "leaf": "A weakly connected endpoint or terminal branch.",
    "isolate": "A minimally integrated region with little transition influence.",
}


def explain_role(role: str) -> str:
    """Explain one normalized structural role."""
    return ROLE_EXPLANATIONS.get(
        role,
        "No structural role explanation has been defined.",
    )


def explain_role_value(role: str, value: float) -> str:
    """Explain a structural role value."""
    if value >= 0.75:
        band = "high"
    elif value >= 0.45:
        band = "moderate"
    else:
        band = "low"

    return f"{role}: {band}. {explain_role(role)}"