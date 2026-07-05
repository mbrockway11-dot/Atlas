
"""Graph Intelligence section for Atlas dossiers."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.layout import divider
from dashboard.ui.metrics import metric_grid


def render_graph_section(profile: dict[str, Any]) -> None:
    """Render Graph Intelligence."""

    divider("Graph Intelligence")

    graph = profile.get("graph_summary", {})

    if not isinstance(graph, dict):
        graph = {}

    raw_nodes = graph.get("raw_node_count", 0)
    raw_edges = graph.get("raw_edge_count", 0)

    truth_nodes = graph.get("truth_node_count", 0)
    truth_edges = graph.get("truth_edge_count", 0)

    reduction = compute_reduction(raw_nodes, truth_nodes)

    metric_grid(
        {
            "Canonical Nodes": raw_nodes,
            "Canonical Edges": raw_edges,
            "Truth Nodes": truth_nodes,
            "Truth Edges": truth_edges,
            "Reduction": reduction,
            "Motif Richness": fmt(graph.get("motif_richness")),
        }
    )

    st.markdown(build_graph_summary(graph))

    render_graph_characteristics(graph)

    render_graph_analysis(graph)


def render_graph_characteristics(graph: dict[str, Any]) -> None:

    divider("Structural Characteristics")

    metric_grid(
        {
            "Topology": graph.get("topology_class", "Unknown"),
            "Dominant Motif": graph.get("dominant_motif", "Unknown"),
            "Primary Axis": graph.get(
                "dominant_topology_axis",
                "Unknown",
            ),
            "Resonance": graph.get(
                "resonance_class",
                "Unknown",
            ),
        }
    )


def render_graph_analysis(graph: dict[str, Any]) -> None:

    divider("Atlas Interpretation")

    st.markdown(
        interpret_graph(graph)
    )


def build_graph_summary(graph: dict[str, Any]) -> str:

    raw_nodes = graph.get("raw_node_count", 0)
    raw_edges = graph.get("raw_edge_count", 0)

    truth_nodes = graph.get("truth_node_count", 0)
    truth_edges = graph.get("truth_edge_count", 0)

    return f"""
The Canonical Identity Graph is Atlas' complete structural representation of identity before deterministic reduction.

This profile generated **{raw_nodes} canonical nodes**
connected through **{raw_edges} canonical relationships**.

After Atlas removes redundant, transient, and low-persistence structures, the Truth Graph preserves **{truth_nodes} persistent nodes** connected through **{truth_edges} essential structural relationships**.

The Truth Graph represents the durable structural architecture used throughout classification, topology, resonance, semantic interpretation, and relationship intelligence.
"""


def interpret_graph(graph: dict[str, Any]) -> str:

    topology = graph.get("topology_class", "Unknown")

    motif = graph.get("dominant_motif", "Unknown")

    axis = graph.get(
        "dominant_topology_axis",
        "Unknown",
    )

    richness = fmt(graph.get("motif_richness"))

    paragraphs = [

f"""
Atlas currently resolves this profile into a
**{topology}**
graph topology.

The dominant organizing motif is
**{motif}**.
""",

f"""
The primary organizing axis is
**{axis}**,
indicating the structural behavior that most consistently survives deterministic reduction.
""",

f"""
Motif richness currently measures
**{richness}**.

Higher motif richness generally indicates a more diverse structural vocabulary, whereas lower values suggest greater specialization around fewer recurring patterns.
""",

"""
Rather than describing personality traits,
the graph describes how information organizes itself inside the identity structure.

Every higher Atlas intelligence layer?including topology, resonance, semantic intelligence, relationship intelligence, and population analysis?is ultimately derived from this graph.
"""

    ]

    return "\n\n".join(paragraphs)


def compute_reduction(raw_nodes: int, truth_nodes: int) -> str:

    try:

        reduction = (
            1.0 - (truth_nodes / raw_nodes)
        ) * 100

        return f"{reduction:.1f}%"

    except Exception:

        return "Unknown"


def fmt(value: Any) -> str:

    try:

        return f"{float(value):.3f}"

    except Exception:

        return "Unknown"
