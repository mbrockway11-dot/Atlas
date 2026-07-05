
"""Structural Genome section for Atlas dossiers."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.layout import divider
from dashboard.ui.metrics import metric_grid


def render_structural_genome_section(profile: dict[str, Any]) -> None:
    """Render structural genome summary."""

    divider("Structural Genome")

    graph_summary = profile.get("graph_summary", {})
    if not isinstance(graph_summary, dict):
        graph_summary = {}

    raw_nodes = graph_summary.get("raw_node_count", 0)
    raw_edges = graph_summary.get("raw_edge_count", 0)
    truth_nodes = graph_summary.get("truth_node_count", 0)
    truth_edges = graph_summary.get("truth_edge_count", 0)

    metric_grid(
        {
            "CIG Nodes": raw_nodes,
            "CIG Edges": raw_edges,
            "STG Nodes": truth_nodes,
            "STG Edges": truth_edges,
            "Dominant Motif": graph_summary.get("dominant_motif", "Unknown"),
            "Motif Richness": fmt(graph_summary.get("motif_richness")),
            "Topology": graph_summary.get("topology_class", "Unknown"),
            "Resonance": graph_summary.get("resonance_class", "Unknown"),
        }
    )

    st.markdown(build_genome_summary(graph_summary))

    with st.expander("Structural Genome Payload", expanded=False):
        st.json(graph_summary)


def build_genome_summary(summary: dict[str, Any]) -> str:
    """Build readable structural genome interpretation."""

    raw_nodes = summary.get("raw_node_count", 0)
    raw_edges = summary.get("raw_edge_count", 0)
    truth_nodes = summary.get("truth_node_count", 0)
    truth_edges = summary.get("truth_edge_count", 0)
    motif = summary.get("dominant_motif", "unknown motif")
    topology = summary.get("topology_class", "unknown topology")
    axis = summary.get("dominant_topology_axis", "unknown axis")
    resonance = summary.get("resonance_class", "unknown resonance")

    return f"""
### Atlas Interpretation

The Structural Genome is the compressed identity architecture produced after Atlas builds and reduces the Kamea-derived graph.

The Canonical Identity Graph contains **{raw_nodes} node(s)** and **{raw_edges} edge(s)** before reduction.

The Structural Truth Graph preserves **{truth_nodes} node(s)** and **{truth_edges} edge(s)** after reduction.

This profile resolves through a **{motif}** dominant motif, a **{topology}** topology, and a primary topology axis of **{axis}**.

The resonance field resolves as **{resonance}**.

The Structural Genome is the comparison object Atlas can use for relationship intelligence, population clustering, similarity search, and long-term profile evolution.
"""


def fmt(value: Any) -> str:
    """Format float."""
    try:
        return f"{float(value):.3f}"
    except Exception:
        return "Unknown"

