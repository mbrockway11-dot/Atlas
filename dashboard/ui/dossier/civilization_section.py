
"""Civilization Function section for Atlas dossiers."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.layout import divider
from dashboard.ui.metrics import metric_grid


def render_civilization_section(profile: dict[str, Any]) -> None:
    """Render civilization-function interpretation."""

    divider("Civilization Function")

    role = profile.get("role", "Unknown")
    subtype = profile.get("subtype", "Unknown")
    function = profile.get("civilization_function", "")
    cognitive_style = profile.get("cognitive_style", "")
    motivation = profile.get("motivation", "")
    growth_path = profile.get("growth_path", "")

    metric_grid(
        {
            "Structural Role": role,
            "Subtype": subtype,
            "Function": function or "Unknown",
        }
    )

    st.markdown(build_civilization_summary(profile))

    render_section("Primary Contribution", function)
    render_section("Cognitive Operating Style", cognitive_style)
    render_section("Motivational Driver", motivation)
    render_section("Development Path", growth_path)

    render_environment_fit(profile)


def render_environment_fit(profile: dict[str, Any]) -> None:
    """Render environment fit."""

    role = str(profile.get("role", ""))

    divider("Best-Fit Environments")

    if role == "Cycle-Weaver":
        items = [
            "Pattern-heavy environments where repeated loops must be detected.",
            "Research, music, symbolic systems, psychology, process work, and iterative design.",
            "Teams that need someone to recognize recurring dynamics before they become problems.",
        ]
    elif role == "Persistence-Architect":
        items = [
            "Long-term system-building environments.",
            "Projects that require continuity, structure, documentation, and durable architecture.",
            "Teams that need someone to preserve coherence across complexity.",
        ]
    elif role == "Pattern-Weaver":
        items = [
            "Interdisciplinary environments with many symbolic or relational inputs.",
            "Research, synthesis, strategy, narrative, and mapping work.",
            "Teams that need hidden relationships translated into usable models.",
        ]
    else:
        items = [
            "Environment fit should be interpreted through the complete structural payload.",
            "Atlas needs more role-specific language for this class.",
        ]

    for item in items:
        st.markdown(f"- {item}")


def build_civilization_summary(profile: dict[str, Any]) -> str:
    """Build summary paragraph."""

    role = profile.get("role", "Unknown")
    subtype = profile.get("subtype", "")
    function = profile.get("civilization_function", "")
    topology = profile.get("topology_class", "unknown topology")
    motif = profile.get("dominant_motif", "unknown motif")

    return f"""
Atlas uses **Civilization Function** to describe what a profile is structurally optimized to contribute.

This profile is classified as **{role}**{f" / **{subtype}**" if subtype else ""}.

{function}

The underlying graph resolves through **{topology}** topology with a **{motif}** dominant motif. This means the person's contribution should be understood as a structural behavior, not merely a personality trait.
"""


def render_section(title: str, value: Any) -> None:
    """Render a section if value exists."""
    if not value:
        return

    st.markdown(f"### {title}")
    st.markdown(str(value))

