
"""Vedic / Natal Intelligence section for Atlas dossiers."""

from __future__ import annotations

from typing import Any

import streamlit as st

from atlas.knowledge.planets import get_planet
from atlas.knowledge.sidereal_signs import get_sidereal_sign
from atlas.knowledge.vedic_interpreter import interpret_planet_placement
from dashboard.ui.layout import divider
from dashboard.ui.metrics import metric_grid


PLANET_ORDER = [
    "sun",
    "moon",
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
    "rahu",
    "ketu",
]


def render_vedic_section(profile: dict[str, Any]) -> None:
    """Render Vedic / Natal Intelligence."""

    divider("Vedic / Natal Intelligence")

    temporal = profile.get("temporal", {})
    classification = profile.get("classification", {})

    if not isinstance(temporal, dict):
        temporal = {}

    planets = extract_planets(temporal)

    if not planets:
        st.info("No natal planet records are available.")
        return

    st.markdown(build_natal_synthesis(profile, planets))

    constellations = extract_astronomical_constellations(temporal)
    if constellations:
        render_astronomical_constellations(constellations)

    for planet in sort_planets(planets):
        render_planet_card(planet, classification)


def extract_astronomical_constellations(
    temporal: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Extract the separate IAU constellation layer from temporal output."""
    natal = temporal.get("natal", {}) if isinstance(temporal.get("natal"), dict) else {}
    ephemeris = natal.get("ephemeris", {}) if isinstance(natal.get("ephemeris"), dict) else {}
    chart = ephemeris.get("astronomical_constellations", {})
    planets = chart.get("planets", {}) if isinstance(chart, dict) else {}
    return planets if isinstance(planets, dict) else {}


def render_astronomical_constellations(
    constellations: dict[str, dict[str, Any]],
) -> None:
    """Render true-sky and 13-constellation ecliptic-path placements."""
    st.markdown("### Astronomical Constellations — IAU Boundaries")
    st.caption(
        "This is a separate astronomical layer, not the 12-sign Vedic zodiac. "
        "The ecliptic path crosses 13 unequal constellations, including Ophiuchus."
    )

    rows = []
    for planet in PLANET_ORDER:
        record = constellations.get(planet.title()) or constellations.get(planet)
        if not isinstance(record, dict):
            continue
        rows.append(
            {
                "Planet": planet.title(),
                "Actual sky constellation": record.get(
                    "actual_constellation", "unknown"
                ),
                "Projected on ecliptic": record.get(
                    "ecliptic_path_constellation", "unknown"
                ),
                "Ophiuchus": "yes" if record.get("is_ophiuchus") else "",
            }
        )

    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)


def extract_planets(temporal: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract planet records from temporal payload."""

    natal = temporal.get("natal", {}) if isinstance(temporal.get("natal"), dict) else {}
    ephemeris = natal.get("ephemeris", {}) if isinstance(natal.get("ephemeris"), dict) else {}
    sidereal = natal.get("sidereal", {}) if isinstance(natal.get("sidereal"), dict) else {}

    for source in [
        sidereal.get("planets"),
        ephemeris.get("planets"),
        sidereal.get("planetary_positions"),
        ephemeris.get("planetary_positions"),
    ]:
        if isinstance(source, list):
            return [item for item in source if isinstance(item, dict)]

        if isinstance(source, dict):
            return [
                {"planet": key, **value}
                if isinstance(value, dict)
                else {"planet": key, "value": value}
                for key, value in source.items()
            ]

    return []


def sort_planets(planets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort planets in traditional display order."""

    def key(item: dict[str, Any]) -> int:
        name = str(item.get("planet") or item.get("name") or "").lower()
        try:
            return PLANET_ORDER.index(name)
        except ValueError:
            return len(PLANET_ORDER)

    return sorted(planets, key=key)


def render_planet_card(
    planet_record: dict[str, Any],
    classification: dict[str, Any],
) -> None:
    """Render one planet interpretation card."""

    planet_name = str(
        planet_record.get("planet")
        or planet_record.get("name")
        or "unknown"
    ).lower()

    sign = planet_record.get("sign", "")
    house = planet_record.get("house")
    degree = planet_record.get("degree", planet_record.get("longitude", ""))

    planet_info = get_planet(planet_name)
    sign_info = get_sidereal_sign(str(sign)) if sign else {}

    interpretation = interpret_planet_placement(
        planet_name=planet_name,
        sign=str(sign),
        house=house,
        classification=classification,
    )

    title = f"{planet_info.get('symbol', '')} {planet_info.get('name', planet_name.title())}"

    with st.container(border=True):
        st.markdown(f"### {title}")

        metric_grid(
            {
                "Sign": sign or "unknown",
                "House": house if house is not None else "unknown",
                "Degree": degree if degree != "" else "unknown",
            }
        )

        st.markdown("#### What It Represents")
        st.markdown(planet_info.get("represents", "No planet description available."))

        if sign_info:
            st.markdown(f"#### What {sign_info.get('name', sign)} Represents")
            st.markdown(sign_info.get("description", "No sign description available."))

        st.markdown("#### Atlas Interpretation")
        st.markdown(interpretation.get("summary", ""))

        with st.expander("Raw Planet Data", expanded=False):
            st.json(planet_record)


def build_natal_synthesis(profile: dict[str, Any], planets: list[dict[str, Any]]) -> str:
    """Build Vedic/natal synthesis paragraph."""

    role = profile.get("role", "Unclassified Structural Actor")
    subtype = profile.get("subtype", "")

    planet_names = [
        str(item.get("planet") or item.get("name") or "unknown").title()
        for item in planets
    ]

    return f"""
### Natal Synthesis

The natal layer currently exposes planetary records for **{", ".join(planet_names)}**.

Atlas treats planetary data as an activation and behavioral-context layer. It helps explain how the compiled structural role may express through cognition, emotion, timing, values, action, growth, responsibility, and evolutionary direction.

For this profile, natal data should be read in support of the compiled role **{role}**{f" / **{subtype}**" if subtype else ""}. It does not replace the Kamea-derived graph, topology, resonance, fingerprint, or Structural Classification v2.
"""

