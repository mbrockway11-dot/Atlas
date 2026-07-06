
"""Astrology evidence adapter.

Converts planetary placements into structural-operator evidence instead of prose.
"""

from __future__ import annotations

from typing import Any

from atlas.synthesis.evidence import StructuralEvidence
from atlas.synthesis.adapters.utils import make_record, safe_dict, safe_float


PLANET_FEATURES = {
    "sun": "visible_authorship",
    "moon": "internal_stabilization",
    "mercury": "information_routing",
    "venus": "value_selection",
    "mars": "energy_allocation",
    "jupiter": "expansion_pattern",
    "saturn": "constraint_pattern",
    "uranus": "innovation_pattern",
    "neptune": "abstraction_pattern",
    "pluto": "transformation_pattern",
}

SIGN_MODIFIERS = {
    "aries": "activation_driven_action",
    "taurus": "stability_seeking",
    "gemini": "information_routing",
    "cancer": "internal_stabilization",
    "leo": "visible_authorship",
    "virgo": "structural_selectivity",
    "libra": "value_selection",
    "scorpio": "transformation_pattern",
    "sagittarius": "expansion_pattern",
    "capricorn": "constraint_pattern",
    "aquarius": "innovation_pattern",
    "pisces": "abstraction_pattern",
    "ophiuchus": "transformation_pattern",
}


def collect(payload: dict[str, Any]) -> list[StructuralEvidence]:
    """Collect astrology evidence from natal planetary placements."""
    placements = find_placements(payload)

    if not placements:
        return []

    evidence: list[StructuralEvidence] = []

    for placement in placements:
        planet = normalize(placement.get("planet") or placement.get("name") or "")
        sign = normalize(placement.get("sign") or placement.get("zodiac_sign") or "")

        if not planet:
            continue

        planet_feature = PLANET_FEATURES.get(planet)
        sign_feature = SIGN_MODIFIERS.get(sign)

        confidence = placement_confidence(placement)

        if planet_feature:
            evidence.append(
                make_record(
                    f"astrology.{planet}",
                    planet_feature,
                    sign or placement,
                    confidence,
                )
            )

        if sign_feature:
            evidence.append(
                make_record(
                    f"astrology.{planet}.sign",
                    sign_feature,
                    sign,
                    max(0.55, confidence - 0.08),
                )
            )

        if planet_feature and sign_feature and planet_feature == sign_feature:
            evidence.append(
                make_record(
                    f"astrology.{planet}.convergence",
                    planet_feature,
                    {
                        "planet": planet,
                        "sign": sign,
                        "degree": placement.get("degree"),
                    },
                    min(1.0, confidence + 0.06),
                )
            )

    return evidence


def find_placements(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Find natal planetary placements across known payload shapes."""
    temporal = safe_dict(payload.get("temporal"))
    natal = safe_dict(temporal.get("natal"))
    runtime = safe_dict(temporal.get("runtime"))
    runtime_natal = safe_dict(runtime.get("natal"))

    candidates = [
        natal.get("planets"),
        natal.get("placements"),
        natal.get("planetary_positions"),
        safe_dict(natal.get("ephemeris")).get("planets"),
        safe_dict(natal.get("ephemeris")).get("placements"),
        runtime_natal.get("planets"),
        runtime_natal.get("placements"),
        safe_dict(runtime_natal.get("ephemeris")).get("planets"),
        safe_dict(runtime_natal.get("ephemeris")).get("placements"),
    ]

    for candidate in candidates:
        placements = normalize_placements(candidate)
        if placements:
            return placements

    return []


def normalize_placements(value: Any) -> list[dict[str, Any]]:
    """Normalize placement containers into list of dicts."""
    if isinstance(value, list):
        return [
            item
            for item in value
            if isinstance(item, dict)
        ]

    if isinstance(value, dict):
        output = []
        for key, item in value.items():
            if isinstance(item, dict):
                record = dict(item)
                record.setdefault("planet", key)
                output.append(record)
        return output

    return []


def placement_confidence(placement: dict[str, Any]) -> float:
    """Estimate placement confidence from available fields."""
    confidence = 0.70

    if placement.get("sign") or placement.get("zodiac_sign"):
        confidence += 0.08

    if placement.get("degree") is not None:
        confidence += 0.04

    if placement.get("house") is not None:
        confidence += 0.04

    if placement.get("source") or placement.get("ephemeris_status"):
        confidence += 0.02

    return min(0.88, confidence)


def normalize(value: Any) -> str:
    """Normalize astrology labels."""
    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )
