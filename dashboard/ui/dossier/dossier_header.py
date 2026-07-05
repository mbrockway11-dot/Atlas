
"""Dossier header for Atlas profile reports."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_dossier_header(profile: dict[str, Any]) -> None:
    """Render top dossier identity header."""

    name = profile.get("name", "Unknown Profile")
    role = profile.get("role", "Unknown Role")
    subtype = profile.get("subtype", "")
    confidence = profile.get("confidence", "Unknown")

    st.markdown(f"# {name}")
    st.markdown("## Atlas Structural Dossier")

    if subtype:
        st.markdown(f"### {role} / {subtype}")
    else:
        st.markdown(f"### {role}")

    st.caption(f"Classification Confidence: {confidence}")

    st.markdown(
        """
This dossier is generated from Atlas canonical compilation, Kamea-derived identity graph construction, structural topology, resonance, fingerprinting, temporal intelligence, and semantic synthesis.
"""
    )
