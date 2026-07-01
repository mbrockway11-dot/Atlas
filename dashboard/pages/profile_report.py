"""Profile Report dashboard page."""

from __future__ import annotations

import streamlit as st

from atlas.services.profile_report_service import (
    build_profile_report_payload,
    json_export,
    list_profile_report_profiles,
)
from atlas.services.temporal_intelligence_service import DEFAULT_TRANSIT_DATE


def render_profile_report_page() -> None:
    """Render canonical Atlas profile report."""
    st.header("Profile Report")
    st.caption(
        "Canonical profile synthesis from library, temporal, graph, "
        "and intelligence layers."
    )

    profiles = list_profile_report_profiles()

    if not profiles:
        st.warning("No saved profiles found.")
        return

    selected = st.selectbox("Profile", profiles)

    transit_date = st.text_input(
        "Transit date",
        value=DEFAULT_TRANSIT_DATE,
    )

    if not st.button("Build Profile Report", type="primary"):
        st.info("Select a profile and build the report.")
        return

    with st.spinner("Building canonical profile report..."):
        payload = build_profile_report_payload(
            selected,
            transit_date=transit_date,
        )

    if not payload.get("success"):
        st.error("Profile report failed.")
        for error in payload.get("errors", []):
            st.error(error)
        st.json(build_safe_payload_export(payload))
        return

    render_metrics(payload)
    render_warnings(payload)
    render_report(payload)
    render_interpretation(payload)
    render_exports(payload)


def render_metrics(payload: dict) -> None:
    """Render report metrics."""
    st.markdown("## Report Health")

    metrics = payload.get("metrics", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ACF", "yes" if metrics.get("has_acf") else "no")
    c2.metric("Intake", "yes" if metrics.get("has_intake") else "no")
    c3.metric("Temporal", "yes" if metrics.get("has_temporal") else "no")
    c4.metric("Graph", "yes" if metrics.get("has_graph") else "no")

    c5, c6, c7 = st.columns(3)
    c5.metric("Sections", metrics.get("section_count", 0))
    c6.metric("Words", metrics.get("report_word_count", 0))
    c7.metric("Missing Artifacts", len(metrics.get("missing_artifacts", [])))

    with st.expander("Raw Metrics", expanded=False):
        st.json(metrics)


def render_warnings(payload: dict) -> None:
    """Render report warnings."""
    warnings = payload.get("warnings", [])
    errors = payload.get("errors", [])

    for warning in warnings:
        st.warning(warning)

    for error in errors:
        st.error(error)


def render_report(payload: dict) -> None:
    """Render Markdown report."""
    st.markdown("## Atlas Report")

    markdown = payload.get("exports", {}).get("markdown", "")

    if not markdown:
        st.info("No Markdown report generated.")
        return

    st.markdown(markdown)


def render_interpretation(payload: dict) -> None:
    """Render structured interpretation."""
    st.markdown("## Structured Interpretation")

    interpretation = payload.get("data", {}).get("interpretation", {})
    sections = interpretation.get("sections", [])

    if not sections:
        st.info("No interpretation sections available.")
        return

    for section in sections:
        title = section.get("title", "Untitled Section")
        summary = section.get("summary", "")
        details = section.get("details", [])

        with st.expander(title, expanded=False):
            if summary:
                st.write(summary)

            if details:
                for detail in details:
                    st.write(f"- {detail}")

            st.json(section)


def render_exports(payload: dict) -> None:
    """Render report exports."""
    st.markdown("## Exports")

    exports = payload.get("exports", {})
    profile_key = payload.get("profile_key", "profile")
    safe_payload = build_safe_payload_export(payload)

    c1, c2, c3 = st.columns(3)

    c1.download_button(
        "Download Markdown",
        data=exports.get("markdown", ""),
        file_name=f"{profile_key}_profile_report.md",
        mime="text/markdown",
    )

    c2.download_button(
        "Download Report JSON",
        data=json_export(exports.get("report_json", {})),
        file_name=f"{profile_key}_profile_report.json",
        mime="application/json",
    )

    c3.download_button(
        "Download Full Payload JSON",
        data=json_export(safe_payload),
        file_name=f"{profile_key}_profile_report_full.json",
        mime="application/json",
    )

    with st.expander("Raw Full Payload", expanded=False):
        st.json(safe_payload)


def build_safe_payload_export(payload: dict) -> dict:
    """Build circular-reference-safe payload for display/download."""
    return {
        "success": payload.get("success"),
        "profile_key": payload.get("profile_key"),
        "profile_dir": payload.get("profile_dir"),
        "transit_date": payload.get("transit_date"),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "metrics": payload.get("metrics", {}),
        "interpretation": payload.get("data", {}).get("interpretation", {}),
        "report": payload.get("data", {}).get("report", {}),
        "library": summarize_layer(payload.get("data", {}).get("library", {})),
        "temporal": summarize_layer(payload.get("data", {}).get("temporal", {})),
        "graph": summarize_layer(payload.get("data", {}).get("graph", {})),
    }


def summarize_layer(layer: dict) -> dict:
    """Summarize a service layer without embedding runtime objects."""
    if not isinstance(layer, dict):
        return {}

    return {
        "success": layer.get("success"),
        "errors": layer.get("errors", []),
        "warnings": layer.get("warnings", []),
        "metrics": layer.get("metrics", {}),
        "exports_keys": sorted(list((layer.get("exports") or {}).keys())),
        "data_keys": sorted(list((layer.get("data") or {}).keys())),
    }
