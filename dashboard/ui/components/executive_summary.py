"""Executive summary component for Atlas dossier."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.components.dossier_common import confidence_label


def render_executive_summary(payload: dict[str, Any]) -> None:
    """Render the top executive structural assessment."""
    identity = payload.get("identity", {})
    classification = payload.get("classification", {})
    topology = payload.get("topology", {})
    resonance = payload.get("resonance", {})
    fingerprint = payload.get("fingerprint", {})

    name = (
        identity.get("display_name")
        or identity.get("name")
        or payload.get("profile_key")
        or "This profile"
    )

    role = classification.get("structural_role", "Unresolved Structural Actor")
    function = classification.get("civilization_function", "")
    confidence = confidence_label(classification.get("confidence"))

    topology_class = topology.get("topology_class", "unresolved topology")
    resonance_class = resonance.get("resonance_class", "unresolved resonance")
    fingerprint_summary = fingerprint.get("summary", {})

    cig_nodes = fingerprint_summary.get("cig_nodes", 0) if isinstance(fingerprint_summary, dict) else 0
    cig_edges = fingerprint_summary.get("cig_edges", 0) if isinstance(fingerprint_summary, dict) else 0

    cognitive_style = classification.get(
        "cognitive_style",
        "This profile is interpreted through compiled structural, temporal, graph, topology, and resonance layers.",
    )

    body = f"""
{name} is compiled by Atlas as a **{role}** with **{confidence}** confidence.

{cognitive_style}

The current structural classification indicates: **{function or "civilization function unresolved."}**

From a graph perspective, the profile currently resolves into a **{topology_class}** topology and a **{resonance_class}** resonance pattern. The compiled fingerprint contains **{cig_nodes} canonical identity graph node(s)** and **{cig_edges} canonical identity graph edge(s)**.

This dossier should be read as a deterministic structural assessment. The compiler produces the measured layers; Atlas interpretation explains how those layers combine into a coherent profile.
""".strip()

    st.markdown("## Executive Structural Assessment")
    with st.container(border=True):
        st.markdown(body)
