
"""Fingerprint Intelligence section."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.layout import divider
from dashboard.ui.metrics import metric_grid


def render_fingerprint_section(profile: dict[str, Any]) -> None:
    """Render Structural Fingerprint."""

    divider("Structural Fingerprint")

    fingerprint = profile.get("fingerprint", {})

    if not isinstance(fingerprint, dict):
        fingerprint = {}

    summary = fingerprint.get("summary", {})

    if not isinstance(summary, dict):
        summary = {}

    metric_grid(
        {
            "CIG Nodes": summary.get("cig_nodes", 0),
            "CIG Edges": summary.get("cig_edges", 0),
            "STG Nodes": summary.get("stg_nodes", 0),
            "STG Edges": summary.get("stg_edges", 0),
            "Dominant Motif": summary.get("dominant_motif", "Unknown"),
            "Topology": summary.get("topology_class", "Unknown"),
            "Resonance": summary.get("resonance_class", "Unknown"),
        }
    )

    st.markdown(build_fingerprint_summary(summary))

    render_uniqueness(profile, summary)


def render_uniqueness(profile: dict[str, Any], summary: dict[str, Any]) -> None:
    """Render uniqueness interpretation."""

    divider("Fingerprint Uniqueness")

    role = profile.get("role", "Unknown")
    subtype = profile.get("subtype", "Unknown")

    st.markdown(
        f"""
This structural fingerprint belongs to the compiled role **{role}**
and subtype **{subtype}**.

Atlas uses this fingerprint as the profile's durable structural signature.
It is not a personality label; it is a compact representation of how the
identity graph reduces into persistent topology, resonance, motif behavior,
and graph structure.
"""
    )

    st.markdown(build_uniqueness_notes(summary))


def build_fingerprint_summary(summary: dict[str, Any]) -> str:
    """Build readable fingerprint summary."""

    cig_nodes = summary.get("cig_nodes", 0)
    cig_edges = summary.get("cig_edges", 0)
    stg_nodes = summary.get("stg_nodes", 0)
    stg_edges = summary.get("stg_edges", 0)
    motif = summary.get("dominant_motif", "Unknown")
    topology = summary.get("topology_class", "Unknown")
    resonance = summary.get("resonance_class", "Unknown")

    return f"""
### Atlas Interpretation

The Structural Fingerprint condenses the full Kamea-derived identity graph into a compact identity signature.

Before reduction, this profile contains **{cig_nodes} canonical identity graph nodes**
and **{cig_edges} canonical identity graph edges**.

After structural reduction, Atlas preserves **{stg_nodes} structural truth graph nodes**
and **{stg_edges} structural truth graph edges**.

The dominant motif is **{motif}**.

The fingerprint currently resolves into a **{topology}** topology with **{resonance}** resonance.

This fingerprint becomes the profile's stable comparison object for relationship intelligence, population clustering, nearest-neighbor search, and structural similarity.
"""


def build_uniqueness_notes(summary: dict[str, Any]) -> str:
    """Build uniqueness notes from graph shape."""

    cig_nodes = safe_int(summary.get("cig_nodes"))
    cig_edges = safe_int(summary.get("cig_edges"))
    stg_nodes = safe_int(summary.get("stg_nodes"))
    stg_edges = safe_int(summary.get("stg_edges"))

    density_note = "Graph density is currently unavailable."

    if cig_nodes > 0:
        density = cig_edges / max(cig_nodes, 1)

        if density >= 4:
            density_note = (
                "The canonical graph is highly relational, producing many "
                "structural links per identity node."
            )
        elif density >= 2:
            density_note = (
                "The canonical graph shows moderate-to-high relational density."
            )
        else:
            density_note = (
                "The canonical graph is relatively sparse, suggesting more selective "
                "structural connection."
            )

    reduction_note = "Reduction profile is currently unavailable."

    if cig_nodes > 0 and stg_nodes > 0:
        retained = stg_nodes / cig_nodes

        if retained >= 0.6:
            reduction_note = (
                "A large portion of the graph survives truth reduction, suggesting "
                "many persistent structures."
            )
        elif retained >= 0.35:
            reduction_note = (
                "Truth reduction preserves a focused subset of the original graph, "
                "suggesting meaningful compression into stable structures."
            )
        else:
            reduction_note = (
                "Truth reduction is highly selective, preserving a compact structural core."
            )

    edge_note = "Truth edge profile is currently unavailable."

    if stg_nodes > 0:
        truth_density = stg_edges / max(stg_nodes, 1)

        if truth_density >= 1:
            edge_note = (
                "The reduced truth graph retains strong internal connectivity."
            )
        else:
            edge_note = (
                "The reduced truth graph favors essential structure over dense connection."
            )

    return f"""
- {density_note}
- {reduction_note}
- {edge_note}
"""


def safe_int(value: Any) -> int:
    """Convert value to int safely."""
    try:
        return int(value)
    except Exception:
        return 0

