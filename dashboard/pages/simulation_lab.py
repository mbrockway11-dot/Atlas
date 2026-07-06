
"""Simulation Lab dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.simulation_lab_service import (
    build_simulation_lab_payload,
    list_simulation_profiles,
    list_simulation_scenarios,
)


ENVIRONMENT_KEYS = [
    "time_pressure",
    "ambiguity",
    "complexity",
    "social_visibility",
    "resource_constraints",
    "conflict",
    "novelty",
    "collaboration",
    "competition",
    "uncertainty",
    "fatigue",
]


def render_simulation_lab_page() -> None:
    """Render Simulation Lab."""
    st.header("Simulation Lab")
    st.caption("Environment -> stimuli -> activation -> propagation -> decision -> recovery -> growth.")

    profiles = list_simulation_profiles()

    if not profiles:
        st.warning("No saved profiles found.")
        return

    c1, c2 = st.columns(2)

    with c1:
        profile_key = st.selectbox(
            "Profile",
            profiles,
            key="simulation_lab_profile",
        )

    with c2:
        scenario = st.selectbox(
            "Scenario preset",
            ["custom"] + list_simulation_scenarios(),
            key="simulation_lab_scenario",
        )

    force = st.toggle("Force recompile", value=False)

    st.markdown("## Environment")

    use_custom = scenario == "custom"
    environment = build_environment_controls(disabled=not use_custom)

    if not st.button("Run Simulation", type="primary"):
        st.info("Choose a profile and scenario, then run the simulation.")
        return

    with st.spinner("Running structural simulation..."):
        payload = build_simulation_lab_payload(
            profile_key,
            scenario="" if use_custom else scenario,
            environment=environment if use_custom else None,
            force=force,
        )

    if not payload.get("success"):
        st.error("Simulation failed.")
        st.json(payload)
        return

    simulation = payload.get("simulation", {})
    render_interpretation(payload)
    render_narrative(simulation)
    render_simulation_summary(simulation)
    render_environment(simulation)
    render_activation(simulation)
    render_decisions(simulation)
    render_recovery_growth(simulation)
    render_flight_recorder(simulation)
    render_raw(simulation)


def build_environment_controls(*, disabled: bool = False) -> dict[str, float]:
    """Render environment sliders."""
    environment = {}

    columns = st.columns(3)

    for index, key in enumerate(ENVIRONMENT_KEYS):
        with columns[index % 3]:
            environment[key] = st.slider(
                key.replace("_", " ").title(),
                min_value=0.0,
                max_value=1.0,
                value=0.5 if not disabled else 0.0,
                step=0.05,
                disabled=disabled,
                key=f"simulation_env_{key}",
            )

    return environment




def render_interpretation(payload: dict) -> None:
    """Render human-readable simulation interpretation."""
    interpretation = payload.get("interpretation", {})

    st.markdown("## Simulation Interpretation")

    st.subheader(interpretation.get("headline", "Likely response unresolved"))
    st.write(interpretation.get("plain_english", ""))
    st.info(interpretation.get("interpretation", ""))

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### What activated")
        activated = interpretation.get("what_activated", [])
        if activated:
            for item in activated:
                st.write(f"- {item}")

    with c2:
        st.markdown("### Likely behavior")
        for item in interpretation.get("likely_behavior", []):
            st.write(f"- {item}")

    st.markdown("### Recovery path")
    st.write(interpretation.get("recovery_summary", ""))

    st.markdown("### Growth path")
    st.write(interpretation.get("growth_summary", ""))



def render_narrative(simulation: dict) -> None:
    """Render simulation narrative."""
    narrative = simulation.get("narrative", {})

    st.markdown("## If This Scenario Occurred...")

    st.subheader(narrative.get("title", "Scenario Walkthrough"))
    st.write(narrative.get("walkthrough", ""))

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Watch For")
        for item in narrative.get("watch_for", []):
            st.warning(item)

    with c2:
        st.markdown("### Highest Leverage Action")
        st.success(narrative.get("highest_leverage_action", ""))

    st.markdown("### Recovery Narrative")
    st.write(narrative.get("recovery_narrative", ""))

    st.markdown("### Growth Narrative")
    st.write(narrative.get("growth_narrative", ""))

    st.caption(narrative.get("confidence_note", ""))

def render_simulation_summary(simulation: dict) -> None:
    """Render top-level simulation summary."""
    st.markdown("## Simulation Output")

    sim = simulation.get("simulation", {})
    decisions = sim.get("decisions", {})
    likely = decisions.get("likely_action") or {}
    propagation = sim.get("propagation", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Likely Action", likely.get("action", "n/a"))
    c2.metric("Action Score", format_number(likely.get("score")))
    c3.metric("Top Activated Nodes", len(propagation.get("top_activated", [])))


def render_environment(simulation: dict) -> None:
    """Render environment and stimuli."""
    sim = simulation.get("simulation", {})
    env = sim.get("environment", {})
    stimuli = sim.get("stimuli", {}).get("stimuli", {})

    st.markdown("## Environment & Stimuli")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Environment")
        st.dataframe(dict_to_frame(env, "variable", "intensity"), width="stretch")

    with c2:
        st.markdown("### Structural Stimuli")
        st.dataframe(dict_to_frame(stimuli, "feature", "activation"), width="stretch")


def render_activation(simulation: dict) -> None:
    """Render activation and propagation."""
    sim = simulation.get("simulation", {})
    activation = sim.get("activation", {})
    propagation = sim.get("propagation", {})

    st.markdown("## Activation Graph")

    active_nodes = activation.get("active_nodes", [])
    top_activated = propagation.get("top_activated", [])

    tabs = st.tabs(["Initial Activation", "After Propagation"])

    with tabs[0]:
        render_rows(active_nodes)

    with tabs[1]:
        render_rows(top_activated)


def render_decisions(simulation: dict) -> None:
    """Render decision candidates."""
    decisions = simulation.get("simulation", {}).get("decisions", {})

    st.markdown("## Decision Engine")

    candidates = decisions.get("ranked_candidates", [])

    if not candidates:
        st.info("No decision candidates generated.")
        return

    st.dataframe(pd.DataFrame(candidates), width="stretch")


def render_recovery_growth(simulation: dict) -> None:
    """Render recovery and growth."""
    sim = simulation.get("simulation", {})
    recovery = sim.get("recovery", {})
    adaptation = sim.get("adaptation", {})
    growth = simulation.get("growth", {})

    st.markdown("## Recovery & Growth")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Recovery Path")
        path = recovery.get("recovery_path", [])
        if path:
            st.write(" -> ".join(path))
        st.json(recovery)

    with c2:
        st.markdown("### Growth Model")
        st.write(" -> ".join(growth.get("growth_sequence", [])))
        st.json(
            {
                "adaptation": adaptation,
                "growth": growth,
            }
        )


def render_flight_recorder(simulation: dict) -> None:
    """Render simulation pipeline."""
    st.markdown("## Flight Recorder")

    sequence = [
        "Environment",
        "Stimuli",
        "Activation",
        "Propagation",
        "Decision",
        "Recovery",
        "Adaptation",
        "Growth",
    ]

    st.write(" -> ".join(sequence))


def render_raw(simulation: dict) -> None:
    """Render raw simulation JSON."""
    with st.expander("Raw Simulation JSON", expanded=False):
        st.json(simulation)


def render_rows(rows: list[dict]) -> None:
    """Render row list."""
    if not rows:
        st.info("No rows available.")
        return

    st.dataframe(pd.DataFrame(rows), width="stretch")


def dict_to_frame(data: dict, key_name: str, value_name: str) -> pd.DataFrame:
    """Convert dict to dataframe."""
    rows = [
        {
            key_name: key,
            value_name: value,
        }
        for key, value in data.items()
    ]

    return pd.DataFrame(rows)


def format_number(value) -> str:
    """Format numeric value."""
    try:
        return f"{float(value):.3f}"
    except Exception:
        return "n/a"
