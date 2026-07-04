"""Vedic / natal intelligence section for Atlas dossier."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.components.planet_card import render_planet_card
from dashboard.ui.components.planet_interpreter import (
    build_natal_synthesis,
    extract_planets,
)


def render_vedic_section(payload: dict[str, Any]) -> None:
    """Render Vedic / natal intelligence section."""
    temporal = payload.get("temporal", {})
    if not isinstance(temporal, dict) or temporal.get("status") != "compiled":
        return

    planets = extract_planets(payload)
    classification = payload.get("classification", {})

    st.markdown("## Vedic / Natal Intelligence")

    with st.container(border=True):
        st.markdown("### Natal Synthesis")
        st.markdown(build_natal_synthesis(planets, classification))

    if not planets:
        st.info(
            "Ephemeris is compiled, but detailed planet records are not yet exposed "
            "in the canonical payload."
        )
        return

    for planet in planets:
        render_planet_card(planet, classification)
