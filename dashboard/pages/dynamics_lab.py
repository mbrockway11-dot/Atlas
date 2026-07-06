
"""Dynamics Lab dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.dynamics_service import (
    build_dynamics_payload,
    list_dynamics_profiles,
)


def render_dynamics_lab_page() -> None:
    """Render Unified Dynamics Lab."""
    st.header("Dynamics Lab")
    st.caption("Unified Dynamics ? Kamea Dynamics ? recurrence, attractors, currents, and prediction.")

    profiles = list_dynamics_profiles()

    if not profiles:
        st.warning("No saved profiles found.")
        return

    c1, c2 = st.columns(2)

    with c1:
        profile_key = st.selectbox(
            "Profile",
            profiles,
            key="dynamics_lab_profile",
        )

    with c2:
        force = st.toggle("Force recompile", value=False)

    if not st.button("Build Dynamics Report", type="primary"):
        st.info("Choose a profile and build the Unified Dynamics report.")
        return

    with st.spinner("Building Unified Dynamics report..."):
        payload = build_dynamics_payload(profile_key, force=force)

    if not payload.get("success"):
        st.error("Dynamics report failed.")
        st.json(payload)
        return

    dynamics = payload.get("dynamics", {})

    render_executive_summary(dynamics)
    render_dynamic_signature(dynamics)
    render_identity_field(dynamics)
    render_prediction(dynamics)
    render_reasoning(dynamics)
    render_evidence(dynamics)
    render_kamea_dynamics(dynamics)
    render_raw(dynamics)


def render_executive_summary(dynamics: dict) -> None:
    """Render executive summary."""
    st.markdown("## Executive Summary")
    st.info(dynamics.get("summary", ""))


def render_dynamic_signature(dynamics: dict) -> None:
    """Render dynamic profile signature."""
    st.markdown("## Dynamic Signature")

    profile = dynamics.get("dynamic_profile", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Flow Stability", profile.get("flow_stability", "n/a"))
    c2.metric("Phase Complexity", profile.get("phase_complexity", "n/a"))
    c3.metric("Attractor Density", format_number(profile.get("attractor_density")))

    c4, c5, c6 = st.columns(3)
    c4.metric("Recurrence", format_percent(profile.get("recurrence")))
    c5.metric("Mean Energy", format_number(profile.get("mean_energy")))
    c6.metric("Field Size", f"{profile.get('field_node_count', 0)} nodes / {profile.get('field_edge_count', 0)} currents")


def render_identity_field(dynamics: dict) -> None:
    """Render identity field."""
    st.markdown("## Identity Field")

    field = dynamics.get("identity_field", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Nodes", field.get("node_count", 0))
    c2.metric("Directed Currents", field.get("current_count", 0))
    c3.metric("Field Density", format_number(field.get("field_density")))

    tabs = st.tabs(["Dominant Attractors", "Dominant Currents"])

    with tabs[0]:
        attractors = field.get("dominant_attractors", [])
        if attractors:
            st.dataframe(pd.DataFrame(attractors), width="stretch")
        else:
            st.info("No attractors available.")

    with tabs[1]:
        currents = field.get("dominant_currents", [])
        if currents:
            st.dataframe(pd.DataFrame(currents), width="stretch")
        else:
            st.info("No currents available.")


def render_prediction(dynamics: dict) -> None:
    """Render dynamic prediction."""
    st.markdown("## Dynamic Prediction")

    prediction = dynamics.get("prediction", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Response Mode", prediction.get("likely_dynamic_response", "n/a"))
    c2.metric("Recovery Probability", format_percent(prediction.get("recovery_probability")))
    c3.metric("Perturbation Sensitivity", format_percent(prediction.get("perturbation_sensitivity")))

    st.write(prediction_interpretation(prediction))


def render_reasoning(dynamics: dict) -> None:
    """Render dynamics reasoning."""
    st.markdown("## Dynamic Reasoning")

    reasoning = dynamics.get("reasoning", {})
    inferences = reasoning.get("inferences", [])

    if not inferences:
        st.info("No dynamic inferences generated.")
        return

    for item in inferences:
        with st.expander(item.get("inference", "Inference"), expanded=False):
            st.metric("Confidence", format_percent(item.get("confidence")))
            st.write(item.get("explanation", ""))


def render_evidence(dynamics: dict) -> None:
    """Render dynamics evidence."""
    st.markdown("## Dynamic Evidence")

    evidence = dynamics.get("evidence", [])

    if not evidence:
        st.info("No dynamic evidence available.")
        return

    st.dataframe(pd.DataFrame(evidence), width="stretch")


def render_kamea_dynamics(dynamics: dict) -> None:
    """Render underlying Kamea Dynamics details."""
    st.markdown("## Kamea Dynamics")

    kamea = dynamics.get("dynamic_signature", {}).get("kamea_dynamics", {})

    if not kamea:
        st.info("No Kamea Dynamics payload available.")
        return

    st.info(kamea.get("summary", ""))

    streams = kamea.get("streams", [])

    c1, c2, c3 = st.columns(3)
    c1.metric("Streams", kamea.get("stream_count", len(streams)))
    c2.metric("Field Nodes", kamea.get("flow_field", {}).get("node_count", 0))
    c3.metric("Directed Currents", kamea.get("flow_field", {}).get("edge_count", 0))

    stream_rows = []

    for stream in streams:
        recurrence = stream.get("recurrence", {})
        attractors = stream.get("attractors", {})
        energy = stream.get("transition_energy", {})

        stream_rows.append(
            {
                "stream_id": stream.get("stream_id"),
                "cipher": stream.get("cipher"),
                "planet": stream.get("planet"),
                "recurrence": recurrence.get("recurrence_ratio"),
                "max_depth": recurrence.get("max_visit_depth"),
                "node_attractors": attractors.get("node_attractor_count"),
                "edge_attractors": attractors.get("edge_attractor_count"),
                "mean_energy": energy.get("mean_energy"),
                "max_energy": energy.get("max_energy"),
            }
        )

    if stream_rows:
        st.markdown("### Stream Table")
        st.dataframe(pd.DataFrame(stream_rows), width="stretch")

    with st.expander("Flow Field", expanded=False):
        st.json(kamea.get("flow_field", {}))


def render_raw(dynamics: dict) -> None:
    """Render raw Dynamics JSON."""
    with st.expander("Raw Unified Dynamics JSON", expanded=False):
        st.json(dynamics)


def prediction_interpretation(prediction: dict) -> str:
    """Translate prediction into plain English."""
    mode = prediction.get("likely_dynamic_response")

    if mode == "activated_recovery_loop":
        return (
            "Interpretation: pressure is likely to activate the system strongly, "
            "but recurrence and attractor density suggest it can reorganize back into a stable pattern."
        )

    if mode == "stable_basin_recovery":
        return (
            "Interpretation: the system is likely to recover through stable attractor basins with relatively low disruption."
        )

    if mode == "flow_disruption_risk":
        return (
            "Interpretation: the system may be sensitive to perturbation and could leave its normal recovery basin under pressure."
        )

    return "Interpretation: the dynamic response is mixed or context-dependent."


def format_number(value) -> str:
    """Format number."""
    try:
        return f"{float(value):.3f}"
    except Exception:
        return "n/a"


def format_percent(value) -> str:
    """Format percent."""
    try:
        return f"{float(value) * 100:.1f}%"
    except Exception:
        return "n/a"
