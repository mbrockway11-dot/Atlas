"""Planet card renderer for Atlas dossier."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.components.dossier_common import data_expander, key_value_grid
from dashboard.ui.components.planet_interpreter import build_planet_interpretation


def render_planet_card(
    planet: dict[str, Any],
    classification: dict[str, Any],
) -> None:
    """Render one planet card."""
    interpretation = build_planet_interpretation(planet, classification)

    title = f"{planet.get('symbol', '○')} {planet.get('name', 'Planet')} — {planet.get('domain', '')}"

    with st.container(border=True):
        st.markdown(f"### {title}")

        st.markdown("**What It Represents**")
        st.markdown(interpretation.get("represents", ""))

        st.markdown("**Compiler Placement**")
        st.markdown(interpretation.get("placement", ""))

        placement_metrics = {
            "Sign": planet.get("sign"),
            "House": planet.get("house"),
            "Degree": planet.get("degree"),
            "Nakshatra": planet.get("nakshatra"),
            "Dignity": planet.get("dignity"),
        }
        key_value_grid({k: v for k, v in placement_metrics.items() if v not in (None, "")}, columns=5)

        question = interpretation.get("structural_question")
        if question:
            st.markdown("**Structural Question**")
            st.markdown(question)

        st.markdown("**Contribution to Structural Role**")
        st.markdown(interpretation.get("role_bridge", ""))

        data_expander("Raw Planet Data", planet.get("raw", {}), expanded=False)
