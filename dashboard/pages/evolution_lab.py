
"""Evolution Lab dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.evolution_lab_service import (
    build_evolution_lab_payload,
    list_evolution_profiles,
    list_evolution_scenarios,
)


def render_evolution_lab_page() -> None:
    """Render Evolution Lab."""
    st.header("Evolution Lab")
    st.caption("Run multiple simulations and model how the cognitive twin adapts over time.")

    profiles = list_evolution_profiles()

    if not profiles:
        st.warning("No saved profiles found.")
        return

    c1, c2 = st.columns(2)

    with c1:
        profile_key = st.selectbox(
            "Profile",
            profiles,
            key="evolution_lab_profile",
        )

    with c2:
        force = st.toggle("Force recompile", value=False)

    scenario_options = list_evolution_scenarios()

    scenarios = st.multiselect(
        "Experience sequence",
        scenario_options,
        default=default_scenarios(scenario_options),
        key="evolution_lab_scenarios",
    )

    if not scenarios:
        st.warning("Choose at least one scenario.")
        return

    if not st.button("Run Evolution Model", type="primary"):
        st.info("Choose an experience sequence and run the evolution model.")
        return

    with st.spinner("Building evolution model..."):
        payload = build_evolution_lab_payload(
            profile_key,
            scenarios,
            force=force,
        )

    if not payload.get("success"):
        st.error("Evolution model failed.")
        st.json(payload)
        return

    evolution = payload.get("evolution", {})
    simulations = payload.get("simulations", [])

    render_summary(evolution)
    render_experience_timeline(evolution)
    render_memory(evolution)
    render_learning(evolution)
    render_adaptation(evolution)
    render_transitions(evolution)
    render_simulation_history(simulations)
    render_raw(evolution)


def default_scenarios(options: list[str]) -> list[str]:
    """Return useful default scenario sequence."""
    preferred = [
        "public_launch",
        "deep_build",
        "creative_pressure",
    ]

    return [
        item for item in preferred
        if item in options
    ] or options[:3]


def render_summary(evolution: dict) -> None:
    """Render evolution summary."""
    st.markdown("## Evolution Summary")

    st.info(evolution.get("summary", ""))

    learning = evolution.get("learning", {})
    adaptation = evolution.get("adaptation", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Experiences", learning.get("experience_count", 0))
    c2.metric("Learning Signal", learning.get("learning_signal", "n/a"))
    c3.metric("Confidence", format_percent(learning.get("confidence")))

    c4, c5 = st.columns(2)
    c4.metric("Dominant Action", learning.get("dominant_action", "n/a"))
    c5.metric("Adaptation", adaptation.get("adaptation_label", "n/a"))


def render_experience_timeline(evolution: dict) -> None:
    """Render experience timeline."""
    st.markdown("## Experience Timeline")

    experiences = evolution.get("history", {}).get("experiences", [])

    if not experiences:
        st.info("No experience records available.")
        return

    rows = [
        {
            "experience": item.get("experience_id"),
            "scenario": item.get("scenario"),
            "likely_action": item.get("likely_action"),
            "recovery_mode": item.get("recovery_mode"),
            "growth_vector": item.get("growth_vector"),
            "activation_score": item.get("activation_score"),
        }
        for item in experiences
    ]

    st.dataframe(pd.DataFrame(rows), width="stretch")

    st.markdown("### Timeline")
    st.write(
        " -> ".join(
            f"{item.get('scenario')} [{item.get('likely_action')}]"
            for item in experiences
        )
    )


def render_memory(evolution: dict) -> None:
    """Render memory model."""
    st.markdown("## Memory Model")

    memory = evolution.get("memory", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Stored Experiences", len(memory.get("experiences", [])))
    c2.metric("Action Patterns", len(memory.get("action_counts", {})))
    c3.metric("Recovery Patterns", len(memory.get("recovery_counts", {})))

    tabs = st.tabs(["Actions", "Recovery", "Growth"])

    with tabs[0]:
        render_count_table(memory.get("action_counts", {}), "action")

    with tabs[1]:
        render_count_table(memory.get("recovery_counts", {}), "recovery")

    with tabs[2]:
        render_count_table(memory.get("growth_counts", {}), "growth")


def render_learning(evolution: dict) -> None:
    """Render learning model."""
    st.markdown("## Learning Signal")

    learning = evolution.get("learning", {})

    st.json(learning)


def render_adaptation(evolution: dict) -> None:
    """Render adaptation report."""
    st.markdown("## Adaptation State")

    adaptation = evolution.get("adaptation", {})

    st.subheader(adaptation.get("adaptation_label", "Unresolved"))
    st.write(adaptation.get("expected_change", ""))

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Strengthened Features")
        for item in adaptation.get("strengthened_features", []):
            st.write(f"- {item}")

    with c2:
        st.markdown("### Watch For")
        for item in adaptation.get("watch_for", []):
            st.warning(item)


def render_transitions(evolution: dict) -> None:
    """Render transition history."""
    st.markdown("## Transition History")

    transitions = evolution.get("transitions", {}).get("transitions", [])

    if not transitions:
        st.info("No transitions available yet. Add more than one experience.")
        return

    st.dataframe(pd.DataFrame(transitions), width="stretch")


def render_simulation_history(simulations: list[dict]) -> None:
    """Render underlying simulation history."""
    st.markdown("## Simulation History")

    rows = []

    for simulation in simulations:
        sim = simulation.get("simulation", {})
        likely = sim.get("decisions", {}).get("likely_action") or {}
        recovery = sim.get("recovery", {})
        narrative = simulation.get("narrative", {})

        rows.append(
            {
                "scenario": simulation.get("scenario"),
                "likely_action": likely.get("action"),
                "score": likely.get("score"),
                "recovery_mode": recovery.get("recovery_mode"),
                "headline": narrative.get("highest_leverage_action"),
            }
        )

    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch")


def render_raw(evolution: dict) -> None:
    """Render raw JSON."""
    with st.expander("Raw Evolution JSON", expanded=False):
        st.json(evolution)


def render_count_table(counts: dict, label: str) -> None:
    """Render count dictionary."""
    if not counts:
        st.info("No counts available.")
        return

    rows = [
        {
            label: key,
            "count": value,
        }
        for key, value in counts.items()
    ]

    st.dataframe(pd.DataFrame(rows), width="stretch")


def format_percent(value) -> str:
    """Format percent."""
    try:
        return f"{float(value) * 100:.1f}%"
    except Exception:
        return "n/a"
