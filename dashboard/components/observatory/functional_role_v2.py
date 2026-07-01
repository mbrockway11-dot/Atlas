"""Atlas v2 Functional Role component."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.classification.functional_role_v2 import (
    classify_profile_functional_role_v2,
)
from atlas.classification.role_diagnostics import audit_functional_roles_v2
from atlas.research import build_profile_matrix_rows


def render_functional_role_v2(acf: dict) -> None:
    """Render Atlas v2 functional role classification."""
    st.markdown("## Atlas v2 Functional Role")

    rows = build_profile_matrix_rows(acf)
    result = classify_profile_functional_role_v2(rows)
    diagnostics = audit_functional_roles_v2(rows)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Primary Role", result["primary_role"])
    c2.metric("Modifier", result["modifier"])
    c3.metric("Subtype", result["subtype"])
    c4.metric("Confidence", format_float(result["confidence"]))

    if result["is_hybrid"]:
        st.warning("Hybrid profile: top role scores are close.")
    else:
        st.success("Stable primary role detected.")

    render_role_probabilities(result)
    render_modifier_scores(result)
    render_profile_consensus(diagnostics)
    render_layer_results(result)


def render_role_probabilities(result: dict) -> None:
    """Render role probability table and chart."""
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
    """Render modifier score table and chart."""
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


def render_profile_consensus(diagnostics: dict) -> None:
    """Render layer consensus for current profile."""
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


def render_layer_results(result: dict) -> None:
    """Render per-layer v2 classifications."""
    st.markdown("### 21-Layer Classification Results")

    layer_rows = []

    for index, layer in enumerate(result.get("layer_results", []), start=1):
        layer_rows.append(
            {
                "layer": index,
                "primary_role": layer["primary_role"],
                "secondary_role": layer["secondary_role"],
                "modifier": layer["modifier"],
                "subtype": layer["subtype"],
                "confidence": layer["confidence"],
                "is_hybrid": layer["is_hybrid"],
                "strongest_metric": layer["evidence"]["strongest_metric"],
                "strongest_value": layer["evidence"]["strongest_value"],
            }
        )

    if not layer_rows:
        st.info("No layer results available.")
        return

    st.dataframe(pd.DataFrame(layer_rows), width="stretch")


def format_float(value) -> str:
    """Format numeric value safely."""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"


def format_percent(value) -> str:
    """Format numeric value as percent safely."""
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "n/a"
