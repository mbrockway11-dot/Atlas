
"""Systems Engineering Report dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.systems_engineering_report_service import (
    build_systems_report_payload,
    list_systems_report_profiles,
)


def render_systems_engineering_report_page() -> None:
    """Render Systems Engineering Report page."""
    st.header("Systems Engineering Report")
    st.caption("Evidence ? fusion ? consensus ? reasoning ? inference graph.")

    profiles = list_systems_report_profiles()

    if not profiles:
        st.warning("No saved profiles found.")
        return

    profile_key = st.selectbox(
        "Profile",
        profiles,
        key="systems_engineering_profile",
    )

    force = st.toggle("Force recompile", value=False)

    if not st.button("Build Systems Engineering Report", type="primary"):
        st.info("Select a profile and build the report.")
        return

    with st.spinner("Building Systems Engineering Report..."):
        service_payload = build_systems_report_payload(profile_key, force=force)
        payload = service_payload.get("payload", {})
        report = service_payload.get("report", {})

    if not service_payload.get("success"):
        st.error("Systems Engineering Report failed.")
        st.json(service_payload)
        return

    render_executive(report)
    render_reasoning(report)
    render_tensions(report)
    render_consensus(report)
    render_evidence_matrix(report)
    render_symbolism(report)
    render_cognition(report)
    render_behavior(report)
    render_population(report)
    render_diagrams(report)
    render_raw(report)


def render_executive(report: dict) -> None:
    """Render executive summary."""
    executive = report.get("executive", {})

    st.markdown("## Executive Structural Summary")

    c1, c2, c3 = st.columns(3)
    c1.metric("System Class", executive.get("system_class", "n/a"))
    c2.metric("Subtype", executive.get("system_subtype", "n/a"))
    c3.metric(
        "Confidence",
        f"{executive.get('classification_confidence', {}).get('percent', 0)}%",
    )

    c4, c5 = st.columns(2)
    c4.metric("Primary Architecture", executive.get("primary_architecture", "n/a"))
    c5.metric(
        "Architecture Confidence",
        format_percent(executive.get("primary_architecture_confidence")),
    )

    st.write(executive.get("summary", ""))

    with st.expander("Executive JSON", expanded=False):
        st.json(executive)


def render_reasoning(report: dict) -> None:
    """Render reasoning chains."""
    reasoning = report.get("reasoning", {})
    inferences = reasoning.get("strongest_inferences", [])

    st.markdown("## Structural Reasoning")

    if not inferences:
        st.info("No reasoning inferences available.")
        return

    rows = [
        {
            "inference": item.get("inference"),
            "category": item.get("category"),
            "confidence": item.get("confidence"),
            "supporting_features": ", ".join(item.get("supporting_features", [])),
            "explanation": item.get("explanation"),
        }
        for item in inferences
    ]

    st.dataframe(pd.DataFrame(rows), width="stretch")

    for item in inferences[:5]:
        with st.expander(item.get("inference", "Inference"), expanded=False):
            st.write(item.get("explanation", ""))
            st.json(item)


def render_tensions(report: dict) -> None:
    """Render structural tensions."""
    tensions = report.get("tensions", {}).get("tensions", [])

    st.markdown("## Structural Tensions")

    if not tensions:
        st.success("No major structural tensions detected.")
        return

    for item in tensions:
        st.warning(f"{item.get('left')} ? {item.get('right')}")
        st.write(item.get("explanation", ""))


def render_consensus(report: dict) -> None:
    """Render consensus section."""
    consensus = report.get("consensus", {})

    st.markdown("## Consensus Themes")

    tabs = st.tabs(["Dominant", "Strong", "Moderate", "Category Summary"])

    with tabs[0]:
        render_theme_table(consensus.get("dominant_themes", []))

    with tabs[1]:
        render_theme_table(consensus.get("strong_themes", []))

    with tabs[2]:
        render_theme_table(consensus.get("moderate_themes", []))

    with tabs[3]:
        summary = consensus.get("category_summary", {})
        if summary:
            st.dataframe(pd.DataFrame.from_dict(summary, orient="index"), width="stretch")
        else:
            st.info("No category summary available.")


def render_theme_table(themes: list[dict]) -> None:
    """Render theme table."""
    if not themes:
        st.info("No themes in this tier.")
        return

    rows = [
        {
            "feature": item.get("feature"),
            "category": item.get("category"),
            "consensus_score": item.get("consensus_score"),
            "engine_count": item.get("engine_count"),
            "evidence_count": item.get("evidence_count"),
            "engines": ", ".join(item.get("engines", [])),
        }
        for item in themes
    ]

    st.dataframe(pd.DataFrame(rows), width="stretch")


def render_evidence_matrix(report: dict) -> None:
    """Render evidence matrix."""
    matrix = report.get("evidence_matrix", {})

    st.markdown("## Evidence Matrix")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Evidence", matrix.get("evidence_count", 0))
    c2.metric("Engines", matrix.get("engine_count", 0))
    c3.metric("Features", matrix.get("feature_count", 0))
    c4.metric("Categories", matrix.get("category_count", 0))

    by_engine = matrix.get("by_engine", {})
    engine_rows = [
        {"engine": engine, "evidence_count": len(items)}
        for engine, items in by_engine.items()
    ]

    if engine_rows:
        st.dataframe(pd.DataFrame(engine_rows).sort_values("evidence_count", ascending=False), width="stretch")

    with st.expander("Raw Evidence Matrix", expanded=False):
        st.json(matrix)


def render_symbolism(report: dict) -> None:
    """Render symbolic architecture."""
    symbolism = report.get("symbolism", {})

    st.markdown("## Symbolic Architecture")
    st.metric("Symbolic Evidence", symbolism.get("symbolic_evidence_count", 0))
    st.write("Engines: " + ", ".join(symbolism.get("engines", [])))

    evidence = symbolism.get("evidence", [])
    if evidence:
        rows = [
            {
                "engine": item.get("engine"),
                "feature": item.get("feature"),
                "category": item.get("category"),
                "confidence": item.get("confidence"),
                "value": str(item.get("value")),
            }
            for item in evidence
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch")


def render_cognition(report: dict) -> None:
    """Render cognitive architecture."""
    cognition = report.get("cognition", {})

    st.markdown("## Cognitive Architecture")
    st.write(" ? ".join(cognition.get("flow", [])))
    render_theme_table(cognition.get("themes", []))


def render_behavior(report: dict) -> None:
    """Render behavioral dynamics."""
    behavior = report.get("behavior", {})

    st.markdown("## Behavioral Dynamics")
    st.metric("Decision Style", behavior.get("decision_style", "mixed"))
    render_theme_table(behavior.get("themes", []))


def render_population(report: dict) -> None:
    """Render population position."""
    population = report.get("population", {})

    st.markdown("## Population Position")
    st.metric("Population Evidence", population.get("population_evidence_count", 0))
    render_theme_table(population.get("strongest_themes", []))


def render_diagrams(report: dict) -> None:
    """Render diagram specs."""
    diagrams = report.get("diagrams", {})

    st.markdown("## Systems Diagram")
    st.write(" ? ".join(diagrams.get("pipeline", [])))

    with st.expander("Inference Graph JSON", expanded=False):
        st.json(diagrams.get("inference_graph", {}))


def render_raw(report: dict) -> None:
    """Render raw report."""
    st.markdown("## Exports")

    with st.expander("Raw Systems Engineering Report JSON", expanded=False):
        st.json(report)


def format_percent(value) -> str:
    """Format confidence percentage."""
    try:
        return f"{float(value) * 100:.1f}%"
    except Exception:
        return "n/a"
