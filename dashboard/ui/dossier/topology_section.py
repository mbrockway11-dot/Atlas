
"""Topology Intelligence section."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.layout import divider
from dashboard.ui.metrics import metric_grid


TOPOLOGY_DESCRIPTIONS = {
    "distributed_sparse":
        "Information distributes across multiple persistent hubs rather than concentrating into a single hierarchy. These profiles integrate knowledge across many domains.",

    "cyclic_network":
        "Identity is organized through recurring loops and reinforcing structural motifs. Learning occurs through iteration, refinement, and recurrence.",

    "hierarchical":
        "Information naturally compresses into layered authority structures with strong directional organization.",

    "mesh":
        "Highly interconnected structure emphasizing adaptability and redundancy.",

    "unknown":
        "Topology has not yet been interpreted."
}


AXIS_DESCRIPTIONS = {
    "persistence":
        "Long-term structural stability dominates behavior.",

    "motif_richness":
        "Behavior emerges from recurring structural patterns.",

    "hierarchy":
        "Organization favors layered control.",

    "branching":
        "Identity expands through exploration and diversification.",

    "cyclicity":
        "Growth occurs through recursive iteration.",

    "bottleneck":
        "Small structural changes can influence the entire system.",
}


def render_topology_section(profile: dict[str, Any]) -> None:
    """Render topology intelligence."""

    divider("Topology Intelligence")

    topology = profile.get("topology", {})

    if not isinstance(topology, dict):
        topology = {}

    summary = topology.get("summary", {})

    topology_class = summary.get("topology_class", "unknown")
    axis = summary.get("dominant_axis", "unknown")

    metric_grid(
        {
            "Topology": topology_class,
            "Primary Axis": axis,
            "Flow": summary.get("flow_pattern", "Unknown"),
            "Organization": summary.get("organization_pattern", "Unknown"),
            "Stability": summary.get("stability_pattern", "Unknown"),
            "Motif Count": summary.get("motif_count", 0),
        }
    )

    st.markdown(build_summary(summary))

    render_vector(summary)


def render_vector(summary: dict[str, Any]) -> None:

    divider("Topology Vector")

    vector = summary.get("topology_vector", {})

    if not vector:
        st.info("Topology vector unavailable.")
        return

    metric_grid(
        {
            "Hierarchy": fmt(vector.get("hierarchy")),
            "Persistence": fmt(vector.get("persistence")),
            "Branching": fmt(vector.get("branching")),
            "Motif Richness": fmt(vector.get("motif_richness")),
            "Cyclicity": fmt(vector.get("cyclicity")),
            "Bottleneck": fmt(vector.get("bottleneck")),
        }
    )


def build_summary(summary: dict[str, Any]) -> str:

    topology = summary.get("topology_class", "unknown")
    axis = summary.get("dominant_axis", "unknown")

    topology_text = TOPOLOGY_DESCRIPTIONS.get(
        topology,
        TOPOLOGY_DESCRIPTIONS["unknown"],
    )

    axis_text = AXIS_DESCRIPTIONS.get(
        axis,
        "Atlas has not yet generated an explanation."
    )

    return f"""
### Atlas Interpretation

The current profile resolves into a **{topology}** topology.

{topology_text}

The dominant organizing axis is **{axis}**.

{axis_text}

Topology is derived directly from the reduced Kamea identity graph and represents how persistent structural information organizes itself after deterministic reduction. It is one of the principal inputs into Structural Classification v2 and Relationship Intelligence.
"""


def fmt(value: Any) -> str:

    try:
        return f"{float(value):.3f}"
    except Exception:
        return "0.000"

