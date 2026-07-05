
"""Structural Synthesis section for Atlas dossiers."""

from __future__ import annotations

from typing import Any

import streamlit as st

from atlas.knowledge.structural_synthesis import build_structural_synthesis
from dashboard.ui.layout import divider
from dashboard.ui.metrics import metric_grid


def render_structural_synthesis_section(profile: dict[str, Any]) -> None:
    """Render integrated structural synthesis."""

    divider("Integrated Structural Synthesis")

    synthesis = profile.get("structural_synthesis")

    if not isinstance(synthesis, dict) or not synthesis.get("success"):
        synthesis = build_structural_synthesis(profile)

    metric_grid(
        {
            "Role": synthesis.get("role", "Unknown"),
            "Subtype": synthesis.get("subtype", "Unknown"),
            "Confidence": format_confidence(synthesis.get("confidence", {})),
            "Version": synthesis.get("version", "Unknown"),
        }
    )

    render_block("Executive Intelligence", synthesis.get("executive_synthesis"))
    render_block("Mind Architecture", synthesis.get("mind_architecture"))
    render_block("Decision Style", synthesis.get("decision_style"))
    render_block("Relationship Dynamics", synthesis.get("relationship_dynamics"))
    render_block("Career Expression", synthesis.get("career_expression"))
    render_block("Stress Pattern", synthesis.get("stress_pattern"))
    render_block("Growth Strategy", synthesis.get("growth_strategy"))

    evidence = synthesis.get("evidence", [])
    if evidence:
        with st.expander("Synthesis Evidence", expanded=False):
            st.json(evidence)


def render_block(title: str, body: Any) -> None:
    """Render one synthesis block."""
    if not body:
        return

    st.markdown(f"### {title}")
    st.markdown(str(body))


def format_confidence(confidence: dict[str, Any]) -> str:
    """Format confidence object."""
    if not isinstance(confidence, dict):
        return "Unknown"

    percent = confidence.get("percent")
    label = confidence.get("label", "")

    if percent is None:
        return str(label or "Unknown")

    return f"{percent}% {label}".strip()

