"""Planetary structural explanations."""

from __future__ import annotations


PLANET_EXPLANATIONS = {
    "Saturn": "Structural persistence, compression, reduction survival, and long-term stability.",
    "Jupiter": "Expansion, connectivity, growth, and broad structural reach.",
    "Mars": "Transition force, activation, directional movement, and volatility.",
    "Sun": "Central coherence, organizing identity, and structural visibility.",
    "Venus": "Integration, cohesion, balance, and harmonized topology.",
    "Mercury": "Articulation, exchange, bridge movement, and flexible transitions.",
    "Moon": "Adaptation, redistribution, cyclical movement, and responsive structure.",
}


def explain_planet(planet: str) -> str:
    """Explain one planetary structural vector."""
    return PLANET_EXPLANATIONS.get(
        planet,
        "No planetary explanation has been defined.",
    )


def explain_planet_feature(planet: str, dominant_feature: str) -> str:
    """Explain a planet through its dominant feature."""
    base = explain_planet(planet)

    return (
        f"{planet} describes {base.lower()} "
        f"In this profile, its strongest signal is `{dominant_feature}`."
    )