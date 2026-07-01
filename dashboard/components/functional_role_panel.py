"""Atlas v2 Functional Role panel.

This is the canonical dashboard classification component.

It does not read legacy acf["essence"]["classification"].
It derives classification from:

ACF -> research matrix -> Functional Role v2
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.classification.functional_role_v2 import (
    classify_profile_functional_role_v2,
)
from atlas.classification.role_diagnostics import audit_functional_roles_v2
from atlas.research import build_profile_matrix_rows


def render_functional_role_panel(acf: dict) -> None:
    """Render canonical Atlas v2 functional role panel."""
    st.markdown("## Atlas v2 Functional Role")

    rows = build_profile_matrix_rows(acf)
    result = classify_profile_functional_role_v2(rows)
    diagnostics = audit_functional_roles_v2(rows)

    render_summary(result)
    render_role_probabilities(result)
    render_modifier_scores(result)
    render_consensus(diagnostics)
    render_evidence(result)


def render_summary(result: dict) -> None:
    """Render top-level role summary."""
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Primary Role", result["primary_role"])
    c2.metric("Modifier", result["modifier"])
    c3.metric("Subtype", result["subtype"])
    c4.metric("Confidence", format_float(result["confidence"]))

    if result["is_hybrid"]:
        st.warning("Hybrid profile: top role scores are close.")
    else:
        st.success("Stable primary role detected.")


def render_role_probabilities(result: dict) -> None:
    """Render role probability distribution."""
    st.markdown("### Role Probabilities")

    dataframe = pd.DataFrame(
        [
            {
                "role": role,
                "probability": score,
            }
            for role, score in result["scores"].items()
        ]
    ).sort_values("probability", ascending=False)

    st.dataframe(dataframe, width="stretch")

    st.bar_chart(
        dataframe.set_index("role")["probability"],
        width="stretch",
    )


def render_modifier_scores(result: dict) -> None:
    """Render modifier score distribution."""
    st.markdown("### Modifier Scores")

    dataframe = pd.DataFrame(
        [
            {
                "modifier": modifier,
                "score": score,
            }
            for modifier, score in result["modifier_scores"].items()
        ]
    ).sort_values("score", ascending=False)

    st.dataframe(dataframe, width="stretch")

    st.bar_chart(
        dataframe.head(10).set_index("modifier")["score"],
        width="stretch",
    )


def render_consensus(diagnostics: dict) -> None:
    """Render layer consensus."""
    st.markdown("### Layer Consensus")

    consensus = diagnostics.get("profile_consensus", [])

    if not consensus:
        st.info("No consensus data available.")
        return

    record = consensus[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Role Consensus", format_percent(record["role_consensus"]))
    c2.metric("Modifier Consensus", format_percent(record["modifier_consensus"]))
    c3.metric("Hybrid", str(record["is_hybrid"]))
    c4.metric("Profile Confidence", format_float(record["confidence"]))

    st.dataframe(pd.DataFrame(consensus), width="stretch")


def render_evidence(result: dict) -> None:
    """Render strongest layer evidence summary."""
    st.markdown("### Layer Evidence")

    layer_rows = []

    for index, layer in enumerate(result.get("layer_results", []), start=1):
        evidence = layer.get("evidence", {})

        layer_rows.append(
            {
                "layer": index,
                "primary_role": layer.get("primary_role"),
                "secondary_role": layer.get("secondary_role"),
                "modifier": layer.get("modifier"),
                "subtype": layer.get("subtype"),
                "confidence": layer.get("confidence"),
                "is_hybrid": layer.get("is_hybrid"),
                "strongest_metric": evidence.get("strongest_metric"),
                "strongest_value": evidence.get("strongest_value"),
            }
        )

    if not layer_rows:
        st.info("No layer evidence available.")
        return

    st.dataframe(pd.DataFrame(layer_rows), width="stretch")


def format_float(value) -> str:
    """Format float safely."""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"


def format_percent(value) -> str:
    """Format percent safely."""
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "n/a"
