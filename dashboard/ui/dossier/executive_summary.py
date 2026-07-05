"""Executive structural assessment for Atlas dossiers."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.layout import divider


def render_executive_summary(profile: dict[str, Any]) -> None:
    """Render the executive structural assessment."""

    divider("Executive Structural Assessment")

    st.markdown(build_executive_summary(profile))

    strengths = build_strengths(profile)
    risks = build_risks(profile)
    observations = build_observations(profile)

    left, middle, right = st.columns(3)

    with left:
        st.markdown("#### Primary Strengths")
        for item in strengths:
            st.markdown(f"- {item}")

    with middle:
        st.markdown("#### Structural Risks")
        for item in risks:
            st.markdown(f"- {item}")

    with right:
        st.markdown("#### Key Observations")
        for item in observations:
            st.markdown(f"- {item}")


def build_executive_summary(profile: dict[str, Any]) -> str:
    """Generate the opening intelligence briefing."""

    name = profile.get("name", "Unknown Profile")

    role = profile.get("role", "Unclassified")
    subtype = profile.get("subtype", "")
    confidence = profile.get("confidence", "Unknown")

    topology = profile.get("topology_class", "Unknown")
    axis = profile.get("dominant_axis", "Unknown")
    motif = profile.get("dominant_motif", "Unknown")

    resonance = profile.get("resonance_class", "Unknown")

    graph = profile.get("graph_summary", {})

    raw_nodes = graph.get("raw_node_count", 0)
    raw_edges = graph.get("raw_edge_count", 0)

    truth_nodes = graph.get("truth_node_count", 0)
    truth_edges = graph.get("truth_edge_count", 0)

    motif_richness = graph.get("motif_richness", 0)

    paragraphs = [

f"""
**{name}** is structurally classified by Atlas as a
**{role}**
{subtype if subtype else ""}

The current deterministic compilation resolved this profile with
**{confidence} confidence**.
""",

f"""
The identity graph demonstrates a
**{topology}**
organizational topology centered around the
**{axis}**
axis.

The dominant structural motif is
**{motif}**,
while the resonance field currently resolves as
**{resonance}**.
""",

f"""
Prior to truth reduction, the structural genome contains
**{raw_nodes} canonical identity nodes**
connected through
**{raw_edges} structural relationships**.

After deterministic reduction,
Atlas preserves
**{truth_nodes} truth nodes**
and
**{truth_edges} essential relationships**,
representing the persistent structure of the identity graph.
""",

f"""
Overall motif richness currently measures
**{motif_richness:.3f}**.

Rather than functioning as a personality assessment,
this dossier represents a deterministic structural model generated
from Atlas identity compilation,
graph topology,
resonance analysis,
temporal intelligence,
and semantic interpretation.
"""

    ]

    return "\n\n".join(paragraphs)


def build_strengths(profile: dict[str, Any]) -> list[str]:

    role = profile.get("role", "")

    strengths = []

    if "Architect" in role:
        strengths.extend([
            "Builds durable systems",
            "High structural thinking",
            "Excellent long-term planning",
        ])

    if "Weaver" in role:
        strengths.extend([
            "Recognizes hidden patterns",
            "Strong synthesis ability",
            "Integrates complex ideas",
        ])

    if "Connector" in role:
        strengths.extend([
            "Connects disparate domains",
            "Excellent collaboration",
        ])

    if not strengths:
        strengths.append("Structural profile still developing.")

    return strengths


def build_risks(profile: dict[str, Any]) -> list[str]:

    role = profile.get("role", "")

    risks = []

    if "Architect" in role:
        risks.extend([
            "May overbuild solutions",
            "Can postpone execution while refining",
        ])

    if "Weaver" in role:
        risks.extend([
            "May overanalyze recurring patterns",
            "Can become trapped in recursive thought",
        ])

    if "Interpreter" in role:
        risks.extend([
            "May overemphasize timing",
            "Can wait too long for perfect alignment",
        ])

    if not risks:
        risks.append("No dominant structural risks identified.")

    return risks


def build_observations(profile: dict[str, Any]) -> list[str]:

    graph = profile.get("graph_summary", {})

    observations = []

    if graph.get("raw_node_count", 0):
        observations.append(
            f"{graph['raw_node_count']} canonical graph nodes compiled."
        )

    if graph.get("truth_node_count", 0):
        observations.append(
            f"{graph['truth_node_count']} truth nodes remain after reduction."
        )

    motif = profile.get("dominant_motif")

    if motif:
        observations.append(f"Dominant motif: {motif}")

    topology = profile.get("topology_class")

    if topology:
        observations.append(f"Topology: {topology}")

    return observations