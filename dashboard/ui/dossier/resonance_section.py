
"""Resonance Intelligence section."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.layout import divider
from dashboard.ui.metrics import metric_grid


RESONANCE_DESCRIPTIONS = {
    "low_resonance":
        "Energy propagates conservatively. Structural changes are typically deliberate and stable rather than rapidly cascading.",

    "medium_resonance":
        "Information propagates efficiently while maintaining stability. These profiles balance adaptation with continuity.",

    "high_resonance":
        "Small structural changes may rapidly influence the wider identity graph. These profiles are highly responsive to internal and external signals.",
}


AXIS_DESCRIPTIONS = {
    "activation":
        "Primary behavior emerges from when structures become active.",

    "stability":
        "Behavior is dominated by preserving structural continuity.",

    "propagation":
        "Information naturally spreads through the graph.",

    "channeling":
        "Energy concentrates through preferred structural pathways.",

    "recirculation":
        "Identity repeatedly revisits established structures.",

    "branching":
        "Activation expands into multiple concurrent pathways.",
}


def render_resonance_section(profile: dict[str, Any]) -> None:
    """Render Resonance Intelligence."""

    divider("Resonance Intelligence")

    resonance = profile.get("resonance", {})

    if not isinstance(resonance, dict):
        resonance = {}

    summary = resonance.get("summary", {})

    resonance_class = summary.get("resonance_class", "unknown")
    axis = summary.get("dominant_resonance_axis", "unknown")

    metric_grid(
        {
            "Resonance": resonance_class,
            "Primary Axis": axis,
            "Activation": summary.get("activation_pattern", "Unknown"),
            "Propagation": summary.get("propagation_pattern", "Unknown"),
            "Damping": summary.get("damping_pattern", "Unknown"),
        }
    )

    st.markdown(build_summary(summary))

    render_vector(summary)


def render_vector(summary: dict[str, Any]) -> None:

    divider("Resonance Vector")

    vector = summary.get("resonance_vector", {})

    if not vector:
        st.info("Resonance vector unavailable.")
        return

    metric_grid(
        {
            "Activation": fmt(vector.get("activation")),
            "Propagation": fmt(vector.get("propagation")),
            "Stability": fmt(vector.get("stability")),
            "Recirculation": fmt(vector.get("recirculation")),
            "Channeling": fmt(vector.get("channeling")),
            "Branching": fmt(vector.get("branching")),
        }
    )


def build_summary(summary: dict[str, Any]) -> str:

    resonance = summary.get("resonance_class", "unknown")
    axis = summary.get("dominant_resonance_axis", "unknown")

    resonance_text = RESONANCE_DESCRIPTIONS.get(
        resonance,
        "Atlas has not yet interpreted this resonance profile.",
    )

    axis_text = AXIS_DESCRIPTIONS.get(
        axis,
        "No dominant resonance axis available.",
    )

    return f"""
### Atlas Interpretation

The profile currently resolves into **{resonance}**.

{resonance_text}

The dominant resonance axis is **{axis}**.

{axis_text}

Resonance describes how structural information moves through the reduced identity graph after topology has been established. While topology explains organization, resonance explains behavior.
"""


def fmt(value: Any) -> str:
    try:
        return f"{float(value):.3f}"
    except Exception:
        return "0.000"

