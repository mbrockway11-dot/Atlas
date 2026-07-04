"""Structural classification component for Atlas dossier."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.components.dossier_common import (
    confidence_label,
    data_expander,
    humanize,
    key_value_grid,
)


ROLE_DESCRIPTIONS = {
    "Temporal-Interpreter": {
        "description": (
            "Temporal Interpreters organize reality through timing, sequence, "
            "activation windows, and change across time. They tend to notice "
            "when systems shift, when patterns are emerging, and when action "
            "is most effective."
        ),
        "strengths": [
            "Pattern recognition across time",
            "Sensitivity to timing and transition",
            "Ability to synthesize changing systems",
            "Strategic awareness of sequence and momentum",
        ],
        "challenges": [
            "Over-focusing on signals before acting",
            "Difficulty disengaging from unresolved patterns",
            "Becoming constrained by timing instead of guided by it",
        ],
        "growth": (
            "Growth comes from translating timing awareness into decisive "
            "execution. The goal is to let timing inform action without "
            "allowing analysis to delay embodiment."
        ),
    },
    "Unclassified Structural Actor": {
        "description": (
            "This profile has not yet resolved into a strong structural role. "
            "Atlas has enough information to describe available layers, but "
            "not enough deterministic evidence to assign a confident role."
        ),
        "strengths": [
            "Open classification state",
            "Flexible interpretation pending more data",
        ],
        "challenges": [
            "Limited deterministic classification evidence",
            "Requires additional structural layers or calibration",
        ],
        "growth": (
            "Growth path remains provisional until more layers are available."
        ),
    },
}


def render_classification_card(payload: dict[str, Any]) -> None:
    """Render a rich structural classification card."""
    classification = payload.get("classification", {})
    if not isinstance(classification, dict) or not classification:
        return

    role = classification.get("structural_role", "Unclassified Structural Actor")
    function = classification.get("civilization_function", "")
    confidence = confidence_label(classification.get("confidence"))
    cognitive_style = classification.get("cognitive_style", "")
    basis = classification.get("basis", {})

    role_info = ROLE_DESCRIPTIONS.get(role, build_generic_role_description(role))

    st.markdown("## Structural Classification")

    with st.container(border=True):
        col1, col2 = st.columns([2, 1])
        col1.markdown(f"### {role}")
        col2.metric("Confidence", confidence)

        if function:
            st.markdown(f"**Civilization Function:** {function}")

        if cognitive_style:
            st.markdown(f"**Cognitive Style:** {cognitive_style}")

        st.markdown("### Role Description")
        st.markdown(role_info["description"])

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("### Core Strengths")
            for item in role_info.get("strengths", []):
                st.markdown(f"- {item}")

        with col_b:
            st.markdown("### Developmental Challenges")
            for item in role_info.get("challenges", []):
                st.markdown(f"- {item}")

        growth = role_info.get("growth")
        if growth:
            st.markdown("### Growth Trajectory")
            st.markdown(growth)

        if isinstance(basis, dict) and basis:
            clean_basis = clean_basis_values(basis)
            if clean_basis:
                st.markdown("### Classification Basis")
                key_value_grid(clean_basis, columns=4)

            data_expander("Raw Classification Basis", basis, expanded=False)


def build_generic_role_description(role: str) -> dict[str, Any]:
    """Build fallback role description."""
    clean_role = humanize(role)

    return {
        "description": (
            f"{clean_role} is a structural role produced by the Atlas "
            "classification layer. Detailed role language has not yet been "
            "specialized for this class, but the role should be interpreted "
            "through its supporting topology, resonance, temporal, and "
            "fingerprint evidence."
        ),
        "strengths": [
            "Compiled deterministic classification",
            "Supported by available canonical layers",
        ],
        "challenges": [
            "Role-specific language still requires refinement",
        ],
        "growth": (
            "Growth should be interpreted through the classification basis and "
            "the complete canonical profile payload."
        ),
    }


def clean_basis_values(basis: dict[str, Any]) -> dict[str, Any]:
    """Clean blank/null basis values before display."""
    cleaned: dict[str, Any] = {}

    for key, value in basis.items():
        if value is None or value == "":
            continue
        cleaned[key] = value

    return cleaned
