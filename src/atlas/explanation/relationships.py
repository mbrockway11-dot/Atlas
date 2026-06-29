"""Planet relationship explanations."""

from __future__ import annotations


def explain_relationship(
    planet_a: str,
    planet_b: str,
    similarity: float,
    distance: float,
    agreement: float,
) -> str:
    """Explain one planet relationship."""
    if similarity >= 0.75:
        similarity_phrase = "strong structural alignment"
    elif similarity >= 0.45:
        similarity_phrase = "moderate structural alignment"
    else:
        similarity_phrase = "weak structural alignment"

    return (
        f"{planet_a} ↔ {planet_b} shows {similarity_phrase} "
        f"(similarity {similarity:.4f}, distance {distance:.4f}, "
        f"agreement {agreement:.4f})."
    )