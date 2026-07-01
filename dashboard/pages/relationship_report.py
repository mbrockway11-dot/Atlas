"""Relationship Report dashboard page."""

from __future__ import annotations

import streamlit as st

from atlas.services.relationship_report_service import (
    build_relationship_report_payload,
    list_relationship_report_profiles,
    relationship_json_export,
)


def render_relationship_report_page() -> None:
    """Render canonical Atlas relationship report."""
    st.header("Relationship Report")
    st.caption(
        "Interpret interaction dynamics between two profiles using profile reports, "
        "graph morphology, topology contrast, and service-derived warnings."
    )

    profiles = list_relationship_report_profiles()

    if len(profiles) < 2:
        st.warning("At least two saved profiles are required.")
        return

    col_a, col_b = st.columns(2)

    with col_a:
        profile_a = st.selectbox(
            "Profile A",
            profiles,
            index=0,
            key="relationship_profile_a",
        )

    with col_b:
        profile_b = st.selectbox(
            "Profile B",
            profiles,
            index=1 if len(profiles) > 1 else 0,
            key="relationship_profile_b",
        )

    if profile_a == profile_b:
        st.warning("Select two different profiles.")
        return

    if not st.button("Build Relationship Report", type="primary"):
        st.info("Select two profiles and build the relationship report.")
        return

    with st.spinner("Building relationship report..."):
        payload = build_relationship_report_payload(profile_a, profile_b)

    if not payload.get("success"):
        st.error("Relationship report failed.")
        for error in payload.get("errors", []):
            st.error(error)

        st.json(build_safe_relationship_payload(payload))
        return

    render_metrics(payload)
    render_warnings(payload)
    render_report(payload)
    render_structured_interpretation(payload)
    render_exports(payload)


def render_metrics(payload: dict) -> None:
    """Render relationship metrics."""
    st.markdown("## Relationship Health")

    metrics = payload.get("metrics", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Profile A Temporal", "yes" if metrics.get("profile_a_temporal") else "no")
    c2.metric("Profile B Temporal", "yes" if metrics.get("profile_b_temporal") else "no")
    c3.metric("Profile A Graph", "yes" if metrics.get("profile_a_graph") else "no")
    c4.metric("Profile B Graph", "yes" if metrics.get("profile_b_graph") else "no")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Morphology Class", metrics.get("morphology_class", "n/a"))
    c6.metric("Similarity", format_metric(metrics.get("morphology_similarity")))
    c7.metric("Mutation", format_metric(metrics.get("mutation_score")))
    c8.metric("Readiness", metrics.get("shared_readiness", "unknown"))

    c9, c10 = st.columns(2)
    c9.metric("Warnings", metrics.get("warning_count", 0))
    c10.metric("Errors", metrics.get("error_count", 0))

    with st.expander("Raw Relationship Metrics", expanded=False):
        st.json(metrics)


def render_warnings(payload: dict) -> None:
    """Render warnings and errors."""
    for warning in payload.get("warnings", []):
        st.warning(warning)

    for error in payload.get("errors", []):
        st.error(error)


def render_report(payload: dict) -> None:
    """Render Markdown relationship report."""
    st.markdown("## Atlas Relationship Report")

    markdown = payload.get("exports", {}).get("markdown", "")

    if not markdown:
        st.info("No relationship Markdown report generated.")
        return

    st.markdown(markdown)


def render_structured_interpretation(payload: dict) -> None:
    """Render structured relationship interpretation."""
    st.markdown("## Structured Relationship Interpretation")

    structured = payload.get("data", {}).get("structured_interpretation", {})
    sections = structured.get("sections", [])

    if not sections:
        st.info("No structured relationship sections available.")
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
    """Render relationship report downloads."""
    st.markdown("## Exports")

    exports = payload.get("exports", {})
    profile_a = payload.get("profile_a", "profile_a")
    profile_b = payload.get("profile_b", "profile_b")

    safe_payload = build_safe_relationship_payload(payload)

    c1, c2, c3 = st.columns(3)

    c1.download_button(
        "Download Markdown",
        data=exports.get("markdown", ""),
        file_name=f"{profile_a}_to_{profile_b}_relationship_report.md",
        mime="text/markdown",
    )

    c2.download_button(
        "Download Relationship JSON",
        data=relationship_json_export(exports.get("relationship_json", {})),
        file_name=f"{profile_a}_to_{profile_b}_relationship_report.json",
        mime="application/json",
    )

    c3.download_button(
        "Download Full Payload JSON",
        data=relationship_json_export(safe_payload),
        file_name=f"{profile_a}_to_{profile_b}_relationship_report_full.json",
        mime="application/json",
    )

    with st.expander("Raw Relationship Payload", expanded=False):
        st.json(safe_payload)


def build_safe_relationship_payload(payload: dict) -> dict:
    """Build circular-safe relationship payload."""
    return {
        "success": payload.get("success"),
        "profile_a": payload.get("profile_a"),
        "profile_b": payload.get("profile_b"),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "metrics": payload.get("metrics", {}),
        "structured_interpretation": payload.get("data", {}).get(
            "structured_interpretation",
            {},
        ),
        "profile_a_summary": payload.get("data", {}).get("profile_a", {}),
        "profile_b_summary": payload.get("data", {}).get("profile_b", {}),
        "morphology": payload.get("data", {}).get("morphology", {}),
    }


def format_metric(value) -> str:
    """Format metric values safely."""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"
