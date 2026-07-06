
"""Comparison Lab dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.comparison_lab_service import (
    build_comparison_lab_payload,
    list_comparison_profiles,
    list_comparison_scenarios,
)


def render_comparison_lab_page() -> None:
    """Render Comparison Lab."""
    st.header("Comparison Lab")
    st.caption("Compare two full reasoning systems: themes, inferences, simulations, and evolution patterns.")

    profiles = list_comparison_profiles()

    if len(profiles) < 2:
        st.warning("At least two saved profiles are required for Comparison Lab.")
        return

    c1, c2, c3 = st.columns(3)

    with c1:
        left_profile = st.selectbox(
            "Left Profile",
            profiles,
            index=0,
            key="comparison_lab_left_profile",
        )

    with c2:
        right_index = 1 if len(profiles) > 1 else 0
        right_profile = st.selectbox(
            "Right Profile",
            profiles,
            index=right_index,
            key="comparison_lab_right_profile",
        )

    with c3:
        force = st.toggle("Force recompile", value=False)

    scenario_options = list_comparison_scenarios()

    scenarios = st.multiselect(
        "Simulation scenarios",
        scenario_options,
        default=default_scenarios(scenario_options),
        key="comparison_lab_scenarios",
    )

    if left_profile == right_profile:
        st.warning("Choose two different profiles.")
        return

    if not scenarios:
        st.warning("Choose at least one simulation scenario.")
        return

    if not st.button("Run Comparison 3.0", type="primary"):
        st.info("Choose two profiles and run Comparison 3.0.")
        return

    with st.spinner("Building comparison report..."):
        payload = build_comparison_lab_payload(
            left_profile,
            right_profile,
            scenarios,
            force=force,
        )

    if not payload.get("success"):
        st.error("Comparison failed.")
        st.json(payload)
        return

    comparison = payload.get("comparison", {})

    render_narrative(comparison)
    render_profile_summaries(comparison)
    render_theme_comparison(comparison)
    render_inference_comparison(comparison)
    render_simulation_comparison(comparison)
    render_evolution_comparison(comparison)
    render_dynamic_resonance(comparison)
    render_raw(comparison)


def default_scenarios(options: list[str]) -> list[str]:
    """Return default comparison scenarios."""
    preferred = [
        "public_launch",
        "deep_build",
        "creative_pressure",
    ]

    selected = [
        item for item in preferred
        if item in options
    ]

    return selected or options[:3]


def render_narrative(comparison: dict) -> None:
    """Render comparison narrative."""
    st.markdown("## Comparison Narrative")

    narrative = comparison.get("narrative", {})

    st.subheader(narrative.get("headline", "Comparison unresolved"))
    st.write(narrative.get("overview", ""))

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Structural Read")
        st.write(narrative.get("shared_architecture", ""))
        st.write(narrative.get("inference_path", ""))

    with c2:
        st.markdown("### Behavioral Read")
        st.write(narrative.get("behavioral_response", ""))
        st.write(narrative.get("adaptation_pattern", ""))

    st.markdown("### Watch For")
    for item in narrative.get("watch_for", []):
        st.warning(item)


def render_profile_summaries(comparison: dict) -> None:
    """Render profile summaries."""
    st.markdown("## Profile Summaries")

    left = comparison.get("left_summary", {})
    right = comparison.get("right_summary", {})

    rows = [
        {"side": "Left", **left},
        {"side": "Right", **right},
    ]

    st.dataframe(pd.DataFrame(rows), width="stretch")


def render_theme_comparison(comparison: dict) -> None:
    """Render theme comparison."""
    st.markdown("## Theme Architecture")

    themes = comparison.get("themes", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Theme Similarity", format_number(themes.get("similarity")))
    c2.metric("Shared Themes", themes.get("shared_count", 0))
    c3.metric("Unique Themes", themes.get("left_unique_count", 0) + themes.get("right_unique_count", 0))

    st.info(themes.get("summary", ""))

    tabs = st.tabs(["Shared", "Left Unique", "Right Unique"])

    with tabs[0]:
        render_list_table(themes.get("shared", []), "shared_theme")

    with tabs[1]:
        render_list_table(themes.get("left_unique", []), "left_unique_theme")

    with tabs[2]:
        render_list_table(themes.get("right_unique", []), "right_unique_theme")


def render_inference_comparison(comparison: dict) -> None:
    """Render inference comparison."""
    st.markdown("## Inference Paths")

    inferences = comparison.get("inferences", {})

    c1, c2 = st.columns(2)
    c1.metric("Inference Similarity", format_number(inferences.get("inference_similarity")))
    c2.metric("Tension Similarity", format_number(inferences.get("tension_similarity")))

    st.info(inferences.get("summary", ""))

    tabs = st.tabs(["Shared Inferences", "Left Unique", "Right Unique", "Shared Tensions"])

    with tabs[0]:
        render_list_table(inferences.get("shared_inferences", []), "shared_inference")

    with tabs[1]:
        render_list_table(inferences.get("left_unique_inferences", []), "left_unique_inference")

    with tabs[2]:
        render_list_table(inferences.get("right_unique_inferences", []), "right_unique_inference")

    with tabs[3]:
        render_list_table(inferences.get("shared_tensions", []), "shared_tension")


def render_simulation_comparison(comparison: dict) -> None:
    """Render simulation comparison."""
    st.markdown("## Simulation Response Differences")

    sims = comparison.get("simulation_responses", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Scenarios", sims.get("scenario_count", 0))
    c2.metric("Same Actions", sims.get("same_action_count", 0))
    c3.metric("Action Similarity", format_number(sims.get("action_similarity")))

    st.info(sims.get("summary", ""))

    rows = []

    for row in sims.get("rows", []):
        rows.append(
            {
                "scenario": row.get("scenario"),
                "left_action": row.get("left_action"),
                "right_action": row.get("right_action"),
                "same_action": row.get("same_action"),
                "left_recovery": row.get("left_recovery"),
                "right_recovery": row.get("right_recovery"),
                "left_growth": row.get("left_growth"),
                "right_growth": row.get("right_growth"),
            }
        )

    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch")


def render_evolution_comparison(comparison: dict) -> None:
    """Render evolution comparison."""
    st.markdown("## Evolution Pattern Differences")

    evolution = comparison.get("evolution_patterns", {})

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Left")
        st.metric("Learning Signal", evolution.get("left_learning_signal", "n/a"))
        st.metric("Dominant Action", evolution.get("left_dominant_action", "n/a"))

    with c2:
        st.markdown("### Right")
        st.metric("Learning Signal", evolution.get("right_learning_signal", "n/a"))
        st.metric("Dominant Action", evolution.get("right_dominant_action", "n/a"))

    st.info(evolution.get("summary", ""))



def render_dynamic_resonance(comparison: dict) -> None:
    """Render Dynamic Resonance v2."""
    st.markdown("## Dynamic Resonance v2")

    resonance = comparison.get("dynamic_resonance_v2", {})

    if not resonance:
        st.info("Dynamic Resonance v2 is unavailable.")
        return

    c1, c2 = st.columns(2)
    c1.metric("Dynamic Resonance", format_number(resonance.get("dynamic_resonance")))
    c2.metric("Label", resonance.get("label", "n/a"))

    narrative = resonance.get("narrative", {})
    st.subheader(narrative.get("headline", "Dynamic resonance"))
    st.write(narrative.get("summary", ""))
    st.info(narrative.get("interpretation", ""))

    components = resonance.get("component_scores", {})

    if components:
        rows = [
            {
                "component": key,
                "score": value,
            }
            for key, value in components.items()
        ]
        st.markdown("### Component Scores")
        st.dataframe(pd.DataFrame(rows), width="stretch")

    shared = resonance.get("shared", {})
    differences = resonance.get("differences", {})

    tabs = st.tabs(["Shared Dynamics", "Differences", "Raw Dynamic Resonance"])

    with tabs[0]:
        st.json(shared)

    with tabs[1]:
        st.json(differences)

    with tabs[2]:
        st.json(resonance)

def render_raw(comparison: dict) -> None:
    """Render raw JSON."""
    with st.expander("Raw Comparison v3 JSON", expanded=False):
        st.json(comparison)


def render_list_table(items: list[str], label: str) -> None:
    """Render list as dataframe."""
    if not items:
        st.info("No items available.")
        return

    st.dataframe(
        pd.DataFrame([{label: item} for item in items]),
        width="stretch",
    )


def format_number(value) -> str:
    """Format numeric metric."""
    try:
        return f"{float(value):.3f}"
    except Exception:
        return "n/a"
