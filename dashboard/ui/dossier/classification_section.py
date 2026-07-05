"""Structural Classification section for Atlas dossiers."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.layout import divider
from dashboard.ui.metrics import metric_grid


def render_classification_section(profile: dict[str, Any]) -> None:
    """Render structural classification."""

    divider("Structural Classification")

    role = profile.get("role", "Unknown")
    subtype = profile.get("subtype", "Unknown")
    confidence = profile.get("confidence", "Unknown")

    st.subheader(role)

    if subtype:
        st.caption(subtype)

    metric_grid(
        {
            "Role": role,
            "Subtype": subtype,
            "Confidence": confidence,
        }
    )

    if profile.get("civilization_function"):
        st.markdown("### Civilization Function")
        st.write(profile["civilization_function"])

    if profile.get("cognitive_style"):
        st.markdown("### Cognitive Style")
        st.write(profile["cognitive_style"])

    render_basis(profile)
    render_behavior(profile)


def render_basis(profile: dict[str, Any]) -> None:
    basis = profile.get("classification_basis", {})

    if not isinstance(basis, dict):
        return

    divider("Classification Basis")

    metric_grid(
        {
            "Topology": basis.get("topology_class", "Unknown"),
            "Primary Axis": basis.get("dominant_topology_axis", "Unknown"),
            "Dominant Motif": basis.get("dominant_motif", "Unknown"),
            "Resonance": basis.get("resonance_class", "Unknown"),
            "Motif Richness": _fmt(basis.get("motif_richness")),
            "Ephemeris": "Yes" if basis.get("has_ephemeris") else "No",
        }
    )

    st.info(
        f'''
Atlas classified this profile using deterministic graph analysis.

Topology:
{basis.get("topology_class","Unknown")}

Dominant Axis:
{basis.get("dominant_topology_axis","Unknown")}

Dominant Motif:
{basis.get("dominant_motif","Unknown")}

Canonical Graph:
{basis.get("raw_node_count",0)} nodes /
{basis.get("raw_edge_count",0)} edges

Truth Graph:
{basis.get("truth_node_count",0)} nodes /
{basis.get("truth_edge_count",0)} edges
'''
    )


def render_behavior(profile: dict[str, Any]) -> None:

    sections = [
        ("Primary Motivation", profile.get("motivation")),
        ("Emotional Pattern", profile.get("emotional_pattern")),
        ("Stress Response", profile.get("stress_response")),
        ("Growth Path", profile.get("growth_path")),
    ]

    for title, value in sections:
        if value:
            st.markdown(f"### {title}")
            st.write(value)


def _fmt(value: Any) -> str:
    try:
        return f"{float(value):.3f}"
    except Exception:
        return "Unknown"
