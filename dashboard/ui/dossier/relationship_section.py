
"""Relationship Intelligence section for Atlas dossiers."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.layout import divider
from dashboard.ui.metrics import metric_grid


def render_relationship_section(profile: dict[str, Any]) -> None:
    """Render relationship intelligence preview."""

    divider("Relationship Intelligence")

    role = profile.get("role", "Unknown")
    subtype = profile.get("subtype", "Unknown")
    topology = profile.get("topology_class", "Unknown")
    resonance = profile.get("resonance_class", "Unknown")
    motif = profile.get("dominant_motif", "Unknown")

    metric_grid(
        {
            "Role": role,
            "Subtype": subtype,
            "Topology": topology,
            "Resonance": resonance,
            "Dominant Motif": motif,
        }
    )

    st.markdown(build_relationship_summary(profile))

    render_compatibility_patterns(profile)
    render_friction_patterns(profile)


def build_relationship_summary(profile: dict[str, Any]) -> str:
    """Build relationship summary."""

    role = profile.get("role", "Unknown")
    topology = profile.get("topology_class", "unknown topology")
    resonance = profile.get("resonance_class", "unknown resonance")

    if role == "Cycle-Weaver":
        core = (
            "This profile may perceive recurring emotional and behavioral loops quickly. "
            "In relationship systems, it may notice when the same conversation, wound, desire, or conflict returns in a new form."
        )
    elif role == "Persistence-Architect":
        core = (
            "This profile tends to value continuity, reliability, and durable relational architecture. "
            "Trust may build through repeated proof, shared structure, and long-range consistency."
        )
    elif role == "Pattern-Weaver":
        core = (
            "This profile may relate through symbolic, emotional, or conceptual pattern recognition. "
            "It may naturally connect separate relational signals into a larger map."
        )
    else:
        core = (
            "Relationship intelligence should be interpreted through the complete structural payload."
        )

    return f"""
Atlas Relationship Intelligence describes how this profile may behave inside shared fields.

{core}

The profile currently expresses through **{topology}** topology and **{resonance}** resonance. This means relationship dynamics should be understood as graph interaction: where connection concentrates, where patterns repeat, where activation stabilizes, and where friction emerges.
"""


def render_compatibility_patterns(profile: dict[str, Any]) -> None:
    """Render likely compatible structures."""

    divider("Compatible Structures")

    role = profile.get("role", "")

    if role == "Cycle-Weaver":
        items = [
            "Profiles that can tolerate recurrence without interpreting it as failure.",
            "Strong stabilizers who help loops become rituals, practices, or refinements.",
            "Pattern-aware communicators who can name cycles without escalating them.",
        ]
    elif role == "Persistence-Architect":
        items = [
            "Profiles that respect long-term building and structural continuity.",
            "Adaptive collaborators who can introduce change without destabilizing the system.",
            "Partners who value coherence, documentation, responsibility, and shared direction.",
        ]
    elif role == "Pattern-Weaver":
        items = [
            "Profiles that appreciate symbolic, relational, or conceptual complexity.",
            "Grounded stabilizers who help prune excess connections.",
            "Collaborators who can translate insight into action.",
        ]
    else:
        items = [
            "Compatibility requires relationship comparison against another profile.",
        ]

    for item in items:
        st.markdown(f"- {item}")


def render_friction_patterns(profile: dict[str, Any]) -> None:
    """Render likely friction structures."""

    divider("Potential Friction")

    role = profile.get("role", "")

    if role == "Cycle-Weaver":
        items = [
            "May revisit unresolved patterns until the loop feels complete.",
            "Can become frustrated when others refuse to recognize recurring dynamics.",
            "Needs to distinguish useful recurrence from rumination.",
        ]
    elif role == "Persistence-Architect":
        items = [
            "May resist abrupt relational restructuring.",
            "Can overfunction as the stabilizer of the system.",
            "Needs to allow durable structures to evolve rather than freeze.",
        ]
    elif role == "Pattern-Weaver":
        items = [
            "May overconnect signals and infer too much too quickly.",
            "Can become tangled in complex emotional or symbolic fields.",
            "Needs clean feedback loops and grounded verification.",
        ]
    else:
        items = [
            "Friction patterns remain provisional until role-specific language is expanded.",
        ]

    for item in items:
        st.markdown(f"- {item}")

