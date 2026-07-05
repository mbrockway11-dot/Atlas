"""Structural role ontology."""

from __future__ import annotations


STRUCTURAL_ROLE_ONTOLOGY = {
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


def explain_structural_role(role: str) -> str:
    """Explain one structural role."""
    return STRUCTURAL_ROLE_ONTOLOGY.get(
        role,
        "No structural role explanation has been defined.",
    )


def rank_structural_roles(
    roles: dict[str, float],
) -> list[dict[str, float | str]]:
    """Rank structural roles by strength."""
    ranked = sorted(
        roles.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return [
        {
            "role": role,
            "score": score,
            "description": explain_structural_role(role),
        }
        for role, score in ranked
    ]
