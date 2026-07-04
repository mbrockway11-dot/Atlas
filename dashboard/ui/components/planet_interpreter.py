"""Planet interpretation helpers for Atlas dossier."""

from __future__ import annotations

from typing import Any

from atlas.knowledge.vedic_interpreter import interpret_planet_placement

from dashboard.ui.components.planet_definitions import (
    PLANET_ORDER,
    get_planet_definition,
    normalize_planet_key,
)


def extract_planets(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract planet records from canonical temporal payload.

    The ephemeris shape may evolve, so this function accepts several common
    structures and normalizes them for UI rendering.
    """
    temporal = payload.get("temporal", {})
    natal = temporal.get("natal", {}) if isinstance(temporal, dict) else {}
    ephemeris = natal.get("ephemeris", {}) if isinstance(natal, dict) else {}

    candidates = [
        ephemeris.get("planets") if isinstance(ephemeris, dict) else None,
        ephemeris.get("positions") if isinstance(ephemeris, dict) else None,
        natal.get("planets") if isinstance(natal, dict) else None,
        natal.get("positions") if isinstance(natal, dict) else None,
    ]

    records: list[dict[str, Any]] = []

    for candidate in candidates:
        if isinstance(candidate, dict):
            for name, data in candidate.items():
                record = normalize_planet_record(name, data)
                if record:
                    records.append(record)

        if isinstance(candidate, list):
            for item in candidate:
                if isinstance(item, dict):
                    name = item.get("planet") or item.get("name") or item.get("body")
                    record = normalize_planet_record(name, item)
                    if record:
                        records.append(record)

        if records:
            break

    return sort_planets(dedupe_planets(records))


def normalize_planet_record(name: Any, data: Any) -> dict[str, Any]:
    """Normalize planet record."""
    if not name:
        return {}

    key = normalize_planet_key(str(name))
    definition = get_planet_definition(key)

    if not isinstance(data, dict):
        data = {"value": data}

    return {
        "key": key,
        "name": definition.get("name", str(name).title()),
        "symbol": definition.get("symbol", "○"),
        "domain": definition.get("domain", ""),
        "definition": definition,
        "raw": data,
        "sign": first_present(data, ["sign", "rashi", "zodiac_sign", "sidereal_sign"]),
        "house": first_present(data, ["house", "bhava"]),
        "degree": first_present(data, ["degree", "degrees", "longitude", "position"]),
        "nakshatra": first_present(data, ["nakshatra", "lunar_mansion"]),
        "dignity": first_present(data, ["dignity", "strength", "status"]),
    }


def build_planet_interpretation(
    planet: dict[str, Any],
    classification: dict[str, Any],
) -> dict[str, str]:
    """Build deterministic planet interpretation language."""
    definition = planet.get("definition", {})

    result = interpret_planet_placement(
        planet_name=planet.get("key") or planet.get("name", ""),
        sign=planet.get("sign"),
        house=planet.get("house"),
        nakshatra=planet.get("nakshatra"),
        classification=classification,
    )

    sign_info = result.get("sign") or {}
    house_info = result.get("house") or {}

    placement_parts = []
    if planet.get("sign"):
        placement_parts.append(f"sign: **{planet.get('sign')}**")
    if planet.get("house"):
        placement_parts.append(f"house: **{planet.get('house')}**")
    if planet.get("nakshatra"):
        placement_parts.append(f"nakshatra: **{planet.get('nakshatra')}**")

    if placement_parts:
        placement = "Compiler placement data includes " + ", ".join(placement_parts) + "."
    else:
        placement = (
            "Detailed sign, house, or nakshatra placement is not exposed in the "
            "current canonical payload, but this planet is present in the ephemeris layer."
        )

    sign_meaning = ""
    if sign_info:
        sign_meaning = (
            f"**What {sign_info.get('name')} Represents:** "
            f"{sign_info.get('description', '')}"
        )

    house_meaning = ""
    if house_info:
        house_meaning = (
            f"**House Meaning:** {house_info.get('description', '')}"
        )

    return {
        "represents": str(definition.get("represents", "")),
        "placement": placement,
        "sign_meaning": sign_meaning,
        "house_meaning": house_meaning,
        "structural_question": str(definition.get("structural_question", "")),
        "role_bridge": str(result.get("summary", "")),
    }


def build_natal_synthesis(
    planets: list[dict[str, Any]],
    classification: dict[str, Any],
) -> str:
    """Build a short synthesis of available planetary data."""
    role = classification.get("structural_role", "the compiled structural role")
    available = [planet.get("name", "") for planet in planets if planet.get("name")]

    if not available:
        return (
            "The temporal layer confirms an ephemeris payload, but detailed planet "
            "records are not yet exposed for narrative synthesis."
        )

    planet_list = ", ".join(available[:9])

    return (
        f"The natal layer currently exposes planetary records for {planet_list}. "
        f"These factors should be read as supporting context for the compiled "
        f"**{role}** classification. Atlas treats planetary data as an activation "
        "and behavioral-context layer: it helps explain how structural tendencies "
        "may express, but it does not replace the graph, topology, resonance, or "
        "fingerprint layers."
    )


def first_present(data: dict[str, Any], keys: list[str]) -> Any:
    """Return first present value from a dictionary."""
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def dedupe_planets(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate planets by key."""
    seen: set[str] = set()
    output: list[dict[str, Any]] = []

    for record in records:
        key = record.get("key")
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(record)

    return output


def sort_planets(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort planets by traditional display order."""
    order = {key: index for index, key in enumerate(PLANET_ORDER)}
    return sorted(records, key=lambda item: order.get(item.get("key", ""), 999))
