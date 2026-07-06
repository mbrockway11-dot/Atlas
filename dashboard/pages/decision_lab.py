
"""Decision Lab dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.decision_lab_service import (
    build_decision_lab_payload,
    list_decision_profiles,
    list_decision_scenarios,
)


def render_decision_lab_page() -> None:
    """Render Decision Lab."""
    st.header("Decision Lab")
    st.caption("Compare competing paths through simulation, scoring, recovery, and growth.")

    profiles = list_decision_profiles()

    if not profiles:
        st.warning("No saved profiles found.")
        return

    scenarios = list_decision_scenarios()

    c1, c2 = st.columns(2)

    with c1:
        profile_key = st.selectbox(
            "Profile",
            profiles,
            key="decision_lab_profile",
        )

    with c2:
        force = st.toggle("Force recompile", value=False)

    st.markdown("## Choices")

    choices = render_choice_inputs(scenarios)

    if not st.button("Compare Decision Paths", type="primary"):
        st.info("Enter two or more choices and compare decision paths.")
        return

    with st.spinner("Comparing decision paths..."):
        payload = build_decision_lab_payload(
            profile_key,
            choices,
            force=force,
        )

    if not payload.get("success"):
        st.error("Decision comparison failed.")
        st.json(payload)
        return

    report = payload.get("decision_report", {})

    render_decision_summary(report)
    render_ranking(report)
    render_narrative(report)
    render_choice_details(report)
    render_raw(report)


def render_choice_inputs(scenarios: list[str]) -> list[dict]:
    """Render choice input form."""
    choices = []

    defaults = [
        ("Choice A", scenarios[0] if scenarios else ""),
        ("Choice B", scenarios[1] if len(scenarios) > 1 else (scenarios[0] if scenarios else "")),
    ]

    for index, (default_label, default_scenario) in enumerate(defaults):
        with st.expander(default_label, expanded=True):
            label = st.text_input(
                "Label",
                value=default_label,
                key=f"decision_choice_label_{index}",
            )

            scenario = st.selectbox(
                "Scenario",
                scenarios,
                index=scenarios.index(default_scenario) if default_scenario in scenarios else 0,
                key=f"decision_choice_scenario_{index}",
            )

            notes = st.text_area(
                "Notes",
                value="",
                key=f"decision_choice_notes_{index}",
            )

            choices.append(
                {
                    "choice_id": f"choice_{index + 1}",
                    "label": label,
                    "scenario": scenario,
                    "notes": notes,
                }
            )

    with st.expander("Optional Choice C", expanded=False):
        use_c = st.checkbox("Include Choice C", value=False)

        if use_c:
            label = st.text_input("Label", value="Choice C", key="decision_choice_label_2")
            scenario = st.selectbox("Scenario", scenarios, key="decision_choice_scenario_2")
            notes = st.text_area("Notes", value="", key="decision_choice_notes_2")

            choices.append(
                {
                    "choice_id": "choice_3",
                    "label": label,
                    "scenario": scenario,
                    "notes": notes,
                }
            )

    return choices


def render_decision_summary(report: dict) -> None:
    """Render top-level decision summary."""
    st.markdown("## Decision Summary")

    comparison = report.get("comparison", {})
    winner = comparison.get("winner") or {}

    c1, c2, c3 = st.columns(3)
    c1.metric("Leading Path", winner.get("label", "n/a"))
    c2.metric("Overall Score", format_number(winner.get("overall_score")))
    c3.metric("Alignment Label", winner.get("score_label", "n/a"))

    st.info(comparison.get("summary", ""))


def render_ranking(report: dict) -> None:
    """Render ranking table."""
    st.markdown("## Path Ranking")

    ranking = report.get("comparison", {}).get("ranking", [])

    if not ranking:
        st.info("No ranking available.")
        return

    st.dataframe(pd.DataFrame(ranking), width="stretch")


def render_narrative(report: dict) -> None:
    """Render decision narrative."""
    st.markdown("## Decision Narrative")

    narrative = report.get("narrative", {})

    st.subheader(narrative.get("headline", "Decision path unresolved"))
    st.write(narrative.get("recommendation", ""))

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Why")
        for item in narrative.get("why", []):
            st.write(f"- {item}")

    with c2:
        st.markdown("### Watch For")
        for item in narrative.get("watch_for", []):
            st.warning(item)


def render_choice_details(report: dict) -> None:
    """Render choice simulation details."""
    st.markdown("## Choice Details")

    results = report.get("results", [])

    for item in results:
        choice = item.get("choice", {})
        score = item.get("score", {})
        simulation = item.get("simulation", {})
        narrative = simulation.get("narrative", {})

        with st.expander(choice.get("label", "Choice"), expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Overall", format_number(score.get("overall_score")))
            c2.metric("Growth", format_number(score.get("growth_alignment")))
            c3.metric("Recovery", format_number(score.get("recovery_alignment")))
            c4.metric("Stress", format_number(score.get("stress_load")))

            st.write(narrative.get("walkthrough", ""))
            st.success(narrative.get("highest_leverage_action", ""))

            with st.expander("Raw choice result", expanded=False):
                st.json(item)


def render_raw(report: dict) -> None:
    """Render raw report JSON."""
    with st.expander("Raw Decision Report JSON", expanded=False):
        st.json(report)


def format_number(value) -> str:
    """Format number."""
    try:
        return f"{float(value):.3f}"
    except Exception:
        return "n/a"
