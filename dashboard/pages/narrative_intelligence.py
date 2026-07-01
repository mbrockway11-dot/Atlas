"""Narrative Intelligence dashboard page."""

from __future__ import annotations

import streamlit as st

from atlas.services.narrative_intelligence_service import (
    build_profile_narrative_payload,
    json_export,
    list_narrative_profiles,
)


def render_narrative_intelligence_page() -> None:
    """Render Narrative Intelligence dashboard."""
    st.header("Narrative Intelligence")
    st.caption(
        "Evidence-backed deterministic narrative synthesis with claims, "
        "confidence, cautions, and source-layer metrics."
    )

    profiles = list_narrative_profiles()

    if not profiles:
        st.warning("No saved profiles found.")
        return

    selected = st.selectbox("Profile", profiles)

    if not st.button("Build Narrative Intelligence", type="primary"):
        st.info("Select a profile and build the narrative.")
        return

    with st.spinner("Building Narrative Intelligence v2..."):
        payload = build_profile_narrative_payload(selected)

    if not payload.get("success"):
        st.error("Narrative Intelligence failed.")
        for error in payload.get("errors", []):
            st.error(error)
        st.json(build_safe_payload(payload))
        return

    render_metrics(payload)
    render_warnings(payload)
    render_markdown(payload)
    render_confidence(payload)
    render_sections(payload)
    render_exports(payload)


def render_metrics(payload: dict) -> None:
    """Render narrative metrics."""
    st.markdown("## Narrative Health")

    metrics = payload.get("metrics", {})
    confidence = metrics.get("overall_confidence", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sections", metrics.get("section_count", 0))
    c2.metric("Claims", metrics.get("claim_count", 0))
    c3.metric("Evidence Items", metrics.get("evidence_count", 0))
    c4.metric("Words", metrics.get("word_count", 0))

    c5, c6, c7 = st.columns(3)
    c5.metric("Warnings", metrics.get("warning_count", 0))
    c6.metric("Errors", metrics.get("error_count", 0))
    c7.metric(
        "Overall Confidence",
        f"{confidence.get('percent', 0)}% {confidence.get('label', '')}",
    )

    with st.expander("Raw Narrative Metrics", expanded=False):
        st.json(metrics)


def render_warnings(payload: dict) -> None:
    """Render warnings and errors."""
    for warning in payload.get("warnings", []):
        st.warning(warning)

    for error in payload.get("errors", []):
        st.error(error)


def render_markdown(payload: dict) -> None:
    """Render narrative Markdown."""
    st.markdown("## Atlas Narrative")

    markdown = payload.get("exports", {}).get("markdown", "")

    if not markdown:
        st.info("No narrative Markdown generated.")
        return

    st.markdown(markdown)


def render_confidence(payload: dict) -> None:
    """Render confidence model."""
    st.markdown("## Confidence")

    narrative = payload.get("data", {}).get("narrative", {})
    confidence = narrative.get("confidence", {})

    if not confidence:
        st.info("No confidence data available.")
        return

    cols = st.columns(4)

    for index, key in enumerate(["identity", "temporal", "graph", "overall"]):
        record = confidence.get(key, {})
        cols[index].metric(
            key.title(),
            f"{record.get('percent', 0)}%",
            record.get("label", "unknown"),
        )

    with st.expander("Raw Confidence JSON", expanded=False):
        st.json(confidence)


def render_sections(payload: dict) -> None:
    """Render structured narrative sections."""
    st.markdown("## Structured Narrative")

    narrative = payload.get("data", {}).get("narrative", {})
    sections = narrative.get("sections", [])

    if not sections:
        st.info("No structured narrative sections available.")
        return

    for section in sections:
        title = section.get("title", "Untitled Section")
        summary = section.get("summary", "")
        details = section.get("details", [])
        claims = section.get("claims", [])
        cautions = section.get("cautions", [])

        with st.expander(title, expanded=False):
            if summary:
                st.write(summary)

            if details:
                st.markdown("### Details")
                for detail in details:
                    st.write(f"- {detail}")

            if claims:
                st.markdown("### Claims")
                for item in claims:
                    confidence = item.get("confidence", {})
                    st.write(
                        f"- **{item.get('claim', '')}** "
                        f"({confidence.get('label', 'unknown')}, "
                        f"{confidence.get('percent', 0)}%)"
                    )

                    evidence = item.get("evidence", [])
                    for evidence_item in evidence:
                        st.write(f"  - Evidence: {evidence_item}")

            if cautions:
                st.markdown("### Cautions")
                for caution in cautions:
                    st.warning(caution)

            st.json(section)


def render_exports(payload: dict) -> None:
    """Render narrative exports."""
    st.markdown("## Exports")

    exports = payload.get("exports", {})
    profile_key = payload.get("profile_key", "profile")
    safe_payload = build_safe_payload(payload)

    c1, c2, c3 = st.columns(3)

    c1.download_button(
        "Download Markdown",
        data=exports.get("markdown", ""),
        file_name=f"{profile_key}_narrative_intelligence.md",
        mime="text/markdown",
    )

    c2.download_button(
        "Download Narrative JSON",
        data=json_export(exports.get("narrative_json", {})),
        file_name=f"{profile_key}_narrative_intelligence.json",
        mime="application/json",
    )

    c3.download_button(
        "Download Full Payload JSON",
        data=json_export(safe_payload),
        file_name=f"{profile_key}_narrative_intelligence_full.json",
        mime="application/json",
    )

    with st.expander("Raw Narrative Payload", expanded=False):
        st.json(safe_payload)


def build_safe_payload(payload: dict) -> dict:
    """Build circular-safe narrative payload."""
    return {
        "success": payload.get("success"),
        "profile_key": payload.get("profile_key"),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "metrics": payload.get("metrics", {}),
        "narrative": payload.get("data", {}).get("narrative", {}),
        "profile_report_summary": payload.get("data", {}).get("profile_report", {}),
    }