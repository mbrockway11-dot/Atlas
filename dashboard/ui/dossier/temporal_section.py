
"""Temporal Intelligence section for Atlas dossiers."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.layout import divider
from dashboard.ui.metrics import metric_grid


def render_temporal_section(profile: dict[str, Any]) -> None:
    """Render temporal intelligence."""

    divider("Temporal Intelligence")

    temporal = profile.get("temporal", {})
    if not isinstance(temporal, dict):
        temporal = {}

    natal = temporal.get("natal", {}) if isinstance(temporal.get("natal"), dict) else {}
    ephemeris = natal.get("ephemeris", {}) if isinstance(natal.get("ephemeris"), dict) else {}
    sidereal = natal.get("sidereal", {}) if isinstance(natal.get("sidereal"), dict) else {}

    planets = extract_planets(ephemeris, sidereal)

    metric_grid(
        {
            "Temporal Status": temporal.get("status", "unknown"),
            "Ephemeris": ephemeris.get("ephemeris_status", "unknown"),
            "Planet Count": len(planets),
            "Time Known": temporal.get("birth", {}).get("time_known", "unknown") if isinstance(temporal.get("birth"), dict) else "unknown",
        }
    )

    st.markdown(build_temporal_summary(temporal, planets))

    if planets:
        render_planet_table(planets)


def extract_planets(ephemeris: dict[str, Any], sidereal: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract planet records from available temporal payloads."""

    for source in [
        ephemeris.get("planets"),
        sidereal.get("planets"),
        ephemeris.get("planetary_positions"),
        sidereal.get("planetary_positions"),
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


def render_planet_table(planets: list[dict[str, Any]]) -> None:
    """Render compact planet records."""

    st.markdown("### Natal Planet Records")

    for planet in planets:
        name = planet.get("planet") or planet.get("name") or "Unknown"
        sign = planet.get("sign", "unknown")
        house = planet.get("house", "unknown")
        degree = planet.get("degree", planet.get("longitude", "unknown"))

        with st.container(border=True):
            st.markdown(f"#### {str(name).title()}")
            metric_grid(
                {
                    "Sign": sign,
                    "House": house,
                    "Degree": degree,
                }
            )


def build_temporal_summary(temporal: dict[str, Any], planets: list[dict[str, Any]]) -> str:
    """Build readable temporal summary."""

    status = temporal.get("status", "unknown")
    count = len(planets)

    return f"""
### Atlas Interpretation

The temporal layer is currently **{status}**.

Atlas uses temporal intelligence as a supporting context layer. It helps describe how structural tendencies may activate through timing, natal conditions, planetary context, and future timing windows.

The current payload exposes **{count} planetary record(s)**.

Temporal data does not replace the Kamea-derived graph, topology, resonance, fingerprint, or structural classification. It explains how those structures may express through time.
"""
