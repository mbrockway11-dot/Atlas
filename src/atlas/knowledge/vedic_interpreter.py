"""Compositional Vedic interpretation helpers for Atlas."""

from __future__ import annotations

from typing import Any

from atlas.knowledge.houses import get_house
from atlas.knowledge.planets import get_planet, normalize_planet
from atlas.knowledge.sidereal_signs import get_sidereal_sign


def interpret_planet_placement(
    *,
    planet_name: str,
    sign: Any = None,
    house: Any = None,
    nakshatra: Any = None,
    classification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic planet + sign + house interpretation."""
    classification = classification or {}

    planet_key = normalize_planet(planet_name)
    planet = get_planet(planet_key)
    sign_info = get_sidereal_sign(str(sign)) if sign else None
    house_info = get_house(house) if house not in (None, "") else None

    role = classification.get("structural_role", "the compiled structural role")

    parts: list[str] = []

    parts.append(
        f"{planet['name']} represents {planet['represents']}"
    )

    if sign_info:
        sign_name = sign_info.get("name", str(sign).title())
        sign_theme = sign_info.get("theme") or sign_info.get("core_theme") or "the sign's core symbolic pattern"
        sign_description = sign_info.get("description", "No detailed sign description is available yet.")

        parts.append(
            f"In sidereal {sign_name}, this planetary function expresses through "
            f"{sign_theme}. {sign_description}"
        )

    if house_info:
        parts.append(
            f"In the {house_info['name']}, this expression is routed through "
            f"{house_info['domain'].lower()}: {house_info['description']}"
        )

    if nakshatra:
        parts.append(
            f"The nakshatra field is present as {nakshatra}. A dedicated nakshatra knowledge layer can refine this interpretation further."
        )

    parts.append(
        f"Within the broader Atlas classification of **{role}**, this placement should be read as one channel through which the structural role expresses in lived behavior."
    )

    return {
        "planet": planet,
        "sign": sign_info,
        "house": house_info,
        "nakshatra": nakshatra,
        "role": role,
        "summary": "\n\n".join(parts),
        "evidence": {
            "planet": planet.get("name"),
            "sign": sign_info.get("name") if sign_info else None,
            "house": house_info.get("name") if house_info else None,
            "nakshatra": nakshatra,
            "structural_role": role,
        },
    }
