"""Classification panel component."""

from __future__ import annotations

import streamlit as st


def render_classification_panel(classification: dict) -> None:
    """Render classification output safely across old/new schema."""
    st.markdown("## Classification")

    function = classification.get("function", {})
    expression = classification.get("expression", {})
    structural = classification.get("structural_state", {})
    planetary = classification.get("planetary_topology", {})

    render_legacy_functional_role(function)
    render_expression(expression)
    render_structural_state(structural)
    render_planetary_topology(planetary)

    with st.expander("Raw Classification JSON"):
        st.json(classification)


def render_legacy_functional_role(function: dict) -> None:
    """Render legacy functional-role scoring with warning."""
    st.markdown("### Legacy Functional Role")

    st.warning(
        "Driver / Amplifier / Regulator are legacy TopologyGraph scores. "
        "They predate Atlas v2 IdentityGraph, coherence, reduction, and "
        "structural-attractor metrics. Treat them as backward-compatible "
        "diagnostics, not authoritative Atlas v2 classification."
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Legacy Role", function.get("role", "unknown"))
    c2.metric("Legacy Subtype", function.get("subtype", "legacy"))
    c3.metric("Legacy Confidence", str(function.get("confidence", "legacy")))
    c4.metric("Hybrid Flag", str(function.get("is_hybrid", False)))

    c5, c6, c7, c8 = st.columns(4)

    c5.metric("Legacy Driver", format_float(function.get("driver")))
    c6.metric("Legacy Amplifier", format_float(function.get("amplifier")))
    c7.metric("Legacy Regulator", format_float(function.get("regulator")))
    c8.metric("Legacy Margin", format_float(function.get("margin")))

    st.caption(
        "Known limitation: legacy Driver is mostly single-node outgoing "
        "concentration, while legacy Regulator is inflated by balance, "
        "symmetry, and component containment. This can make Driver appear "
        "low and Regulator appear dominant across many profiles."
    )

    st.write(function.get("reason", "No legacy functional role reason supplied."))


def render_expression(expression: dict) -> None:
    """Render expression classification."""
    st.markdown("### Expression")
    st.write(f"Expression: `{expression.get('expression', 'missing')}`")
    st.write(f"Reason: {expression.get('reason', 'No expression reason supplied.')}")


def render_structural_state(structural: dict) -> None:
    """Render structural-state classification."""
    st.markdown("### Structural State")
    st.write(f"State: `{structural.get('state', 'missing')}`")
    st.write(f"Reason: {structural.get('reason', 'No structural reason supplied.')}")


def render_planetary_topology(planetary: dict) -> None:
    """Render planetary-topology classification."""
    st.markdown("### Planetary Topology")
    st.write(
        f"Planetary Topology: `{planetary.get('planetary_topology', 'missing')}`"
    )
    st.write(f"Reason: {planetary.get('reason', 'No planetary reason supplied.')}")


def format_float(value) -> str:
    """Format numeric values safely."""
    if value is None:
        return "n/a"

    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return str(value)