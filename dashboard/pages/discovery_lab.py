
"""Discovery Lab dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.discovery_service import (
    build_discovery_payload,
    list_discovery_profiles,
)


def render_discovery_lab_page() -> None:
    """Render Discovery Lab."""
    st.header("Discovery Lab")
    st.caption("Atlas self-questioning loop: questions ? correlations ? hypotheses ? ranked insights.")

    profiles = list_discovery_profiles()

    if not profiles:
        st.warning("No saved profiles found.")
        return

    limit = st.slider("Profile limit", 2, max(2, min(100, len(profiles))), min(25, len(profiles)))
    force = st.toggle("Force recompile", value=False)

    selected_profiles = st.multiselect(
        "Optional profile subset",
        profiles,
        default=[],
    )

    use_profiles = selected_profiles or None

    if not st.button("Run Discovery Scan", type="primary"):
        st.info("Run a discovery scan to let Atlas test correlation questions across profiles.")
        return

    with st.spinner("Running Discovery Engine..."):
        payload = build_discovery_payload(
            use_profiles,
            limit=limit if not selected_profiles else None,
            force=force,
        )

    if not payload.get("success"):
        st.error("Discovery scan failed.")
        st.json(payload)
        return

    discovery = payload.get("discovery", {})

    render_summary(payload)
    render_ranked_evidence(discovery)
    render_hypotheses(discovery)
    render_correlations(discovery)
    render_questions(discovery)
    render_raw(discovery)


def render_summary(payload: dict) -> None:
    """Render executive summary."""
    st.markdown("## Discovery Summary")
    st.info(payload.get("summary", ""))

    c1, c2, c3 = st.columns(3)
    c1.metric("Records", payload.get("record_count", 0))
    c2.metric("Hypotheses", len(payload.get("hypotheses", [])))
    c3.metric("Ranked Evidence", len(payload.get("ranked_evidence", [])))


def render_ranked_evidence(discovery: dict) -> None:
    """Render ranked evidence."""
    st.markdown("## Ranked Evidence")

    rows = discovery.get("ranked_evidence", [])

    if not rows:
        st.info("No ranked evidence yet.")
        return

    st.dataframe(pd.DataFrame(rows), width="stretch")


def render_hypotheses(discovery: dict) -> None:
    """Render hypotheses."""
    st.markdown("## Hypotheses")

    hypotheses = discovery.get("hypotheses", [])

    if not hypotheses:
        st.info("No hypotheses crossed the current evidence threshold.")
        return

    for item in hypotheses:
        with st.expander(item.get("hypothesis_id", "Hypothesis"), expanded=False):
            st.write(item.get("hypothesis", ""))
            c1, c2, c3 = st.columns(3)
            c1.metric("Confidence", format_percent(item.get("confidence")))
            c2.metric("Correlation", format_number(item.get("correlation")))
            c3.metric("Sample Size", item.get("sample_size", 0))
            st.json(item.get("evidence", {}))


def render_correlations(discovery: dict) -> None:
    """Render correlation scans."""
    st.markdown("## Correlation Scans")

    scans = discovery.get("correlation_scans", [])

    if not scans:
        st.info("No correlation scans available.")
        return

    rows = []

    for scan in scans:
        rows.append(
            {
                "question_id": scan.get("question_id"),
                "question": scan.get("question"),
                "sample_size": scan.get("sample_size"),
                "correlation": scan.get("correlation"),
                "strength": scan.get("strength"),
                "direction": scan.get("direction"),
                "x_field": scan.get("x_field"),
                "y_field": scan.get("y_field"),
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch")

    with st.expander("Supporting Rows", expanded=False):
        st.json(scans)


def render_questions(discovery: dict) -> None:
    """Render discovery questions."""
    st.markdown("## Questions Asked")

    questions = discovery.get("questions", [])

    if not questions:
        st.info("No questions available.")
        return

    st.dataframe(pd.DataFrame(questions), width="stretch")


def render_raw(discovery: dict) -> None:
    """Render raw discovery JSON."""
    with st.expander("Raw Discovery JSON", expanded=False):
        st.json(discovery)


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
