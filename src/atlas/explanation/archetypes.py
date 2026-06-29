"""Structural archetype explanations."""

from __future__ import annotations

from atlas.ontology.archetypes import STRUCTURAL_ARCHETYPES


def explain_archetype(archetype_key: str) -> str:
    """Explain one structural archetype."""
    archetype = STRUCTURAL_ARCHETYPES.get(archetype_key)

    if archetype is None:
        return "No archetype explanation has been defined."

    metrics = ", ".join(archetype["primary_metrics"])

    return (
        f"{archetype['label']}: {archetype['description']} "
        f"Primary measurements: {metrics}."
    )


def explain_archetype_score(archetype_key: str, score: float) -> str:
    """Explain archetype strength."""
    if score >= 0.75:
        band = "strong"
    elif score >= 0.45:
        band = "moderate"
    else:
        band = "weak"

    return f"{explain_archetype(archetype_key)} Strength: {band} ({score:.4f})."