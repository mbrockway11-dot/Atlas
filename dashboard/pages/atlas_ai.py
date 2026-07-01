"""Atlas AI dashboard page."""

from __future__ import annotations

import streamlit as st

from atlas.services.atlas_ai_service import (
    build_profile_ai_payload,
    build_relationship_ai_payload,
    json_export,
    list_atlas_ai_profiles,
)


def render_atlas_ai_page() -> None:
    """Render Atlas AI page."""
    st.header("Atlas AI")
    st.caption(
        "Deterministic orchestration layer for profile, narrative, evidence, "
        "graph intelligence, temporal, and relationship services."
    )

    profiles = list_atlas_ai_profiles()

    if not profiles:
        st.warning("No saved profiles found.")
        return

    mode = st.radio(
        "AI scope",
        ["Profile", "Relationship"],
        horizontal=True,
        key="atlas_ai_scope",
    )

    if mode == "Profile":
        render_profile_ai_mode(profiles)
    else:
        render_relationship_ai_mode(profiles)


def render_profile_ai_mode(profiles: list[str]) -> None:
    """Render profile Atlas AI mode."""
    profile_key = st.selectbox(
        "Profile",
        profiles,
        key="atlas_ai_profile",
    )

    services = st.multiselect(
        "Services",
        [
            "profile_report",
            "narrative",
            "evidence",
            "graph_intelligence",
            "temporal",
        ],
        default=[
            "profile_report",
            "narrative",
            "evidence",
            "graph_intelligence",
            "temporal",
        ],
        key="atlas_ai_profile_services",
    )

    if not st.button("Run Profile Atlas AI", type="primary"):
        st.info("Select a profile and run Atlas AI.")
        return

    with st.spinner("Running Atlas AI profile orchestration..."):
        payload = build_profile_ai_payload(
            profile_key,
            services=services,
        )

    render_atlas_ai_payload(payload)


def render_relationship_ai_mode(profiles: list[str]) -> None:
    """Render relationship Atlas AI mode."""
    col_a, col_b = st.columns(2)

    with col_a:
        profile_a = st.selectbox(
            "Profile A",
            profiles,
            index=0,
            key="atlas_ai_profile_a",
        )

    with col_b:
        profile_b = st.selectbox(
            "Profile B",
            profiles,
            index=1 if len(profiles) > 1 else 0,
            key="atlas_ai_profile_b",
        )

    services = st.multiselect(
        "Services",
        [
            "relationship_report",
            "relationship_evidence",
            "relationship_graph_intelligence",
        ],
        default=[
            "relationship_report",
            "relationship_evidence",
            "relationship_graph_intelligence",
        ],
        key="atlas_ai_relationship_services",
    )

    if profile_a == profile_b:
        st.warning("Select two different profiles.")
        return

    if not st.button("Run Relationship Atlas AI", type="primary"):
        st.info("Select two profiles and run Atlas AI.")
        return

    with st.spinner("Running Atlas AI relationship orchestration..."):
        payload = build_relationship_ai_payload(
            profile_a,
            profile_b,
            services=services,
        )

    render_atlas_ai_payload(payload)


def render_atlas_ai_payload(payload: dict) -> None:
    """Render Atlas AI payload."""
    if not payload.get("success"):
        st.error("Atlas AI failed.")
        for error in payload.get("errors", []):
            st.error(error)
        st.json(build_safe_payload(payload))
        return

    render_metrics(payload)
    render_warnings(payload)
    render_synthesis(payload)
    render_service_summary(payload)
    render_exports(payload)


def render_metrics(payload: dict) -> None:
    """Render Atlas AI metrics."""
    st.markdown("## Atlas AI Health")

    metrics = payload.get("metrics", {})
    confidence = metrics.get("overall_confidence", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Services", metrics.get("service_count", 0))
    c2.metric("Successful", metrics.get("successful_services", 0))
    c3.metric("Failed", metrics.get("failed_services", 0))
    c4.metric(
        "Overall Confidence",
        format_confidence(confidence),
    )

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Strengths", metrics.get("strength_count", 0))
    c6.metric("Risks", metrics.get("risk_count", 0))
    c7.metric("Priorities", metrics.get("priority_count", 0))
    c8.metric("Warnings", metrics.get("warning_count", 0))

    with st.expander("Raw Atlas AI Metrics", expanded=False):
        st.json(metrics)


def render_warnings(payload: dict) -> None:
    """Render Atlas AI warnings and errors."""
    for warning in payload.get("warnings", []):
        st.warning(warning)

    for error in payload.get("errors", []):
        st.error(error)


def render_synthesis(payload: dict) -> None:
    """Render Atlas AI synthesis."""
    synthesis = payload.get("data", {}).get("synthesis", {})

    st.markdown("## Atlas AI Synthesis")

    executive = synthesis.get("executive_summary", "")
    if executive:
        st.success(executive)

    confidence = synthesis.get("confidence", {})
    if confidence:
        st.markdown("### Confidence")
        st.json(confidence)

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("### Strengths")
        for item in synthesis.get("strengths", []):
            st.write(f"- {item}")

    with col_b:
        st.markdown("### Risks")
        for item in synthesis.get("risks", []):
            st.write(f"- {item}")

    with col_c:
        st.markdown("### Research Priorities")
        for item in synthesis.get("research_priorities", []):
            st.write(f"- {item}")

    markdown = payload.get("exports", {}).get("markdown", "")

    if markdown:
        st.markdown("## Atlas AI Report")
        st.markdown(markdown)


def render_service_summary(payload: dict) -> None:
    """Render service summary."""
    st.markdown("## Service Summary")

    synthesis = payload.get("data", {}).get("synthesis", {})
    service_summary = synthesis.get("service_summary", {})

    if not service_summary:
        st.info("No service summary available.")
        return

    rows = []

    for name, summary in service_summary.items():
        rows.append(
            {
                "service": name,
                "success": summary.get("success"),
                "errors": summary.get("error_count"),
                "warnings": summary.get("warning_count"),
            }
        )

    st.dataframe(rows, width="stretch")

    with st.expander("Raw Service Summary", expanded=False):
        st.json(service_summary)


def render_exports(payload: dict) -> None:
    """Render Atlas AI exports."""
    st.markdown("## Exports")

    safe_payload = build_safe_payload(payload)

    c1, c2, c3 = st.columns(3)

    c1.download_button(
        "Download Markdown",
        data=payload.get("exports", {}).get("markdown", ""),
        file_name="atlas_ai_report.md",
        mime="text/markdown",
    )

    c2.download_button(
        "Download AI JSON",
        data=json_export(payload.get("exports", {}).get("ai_json", {})),
        file_name="atlas_ai.json",
        mime="application/json",
    )

    c3.download_button(
        "Download Full Payload JSON",
        data=json_export(safe_payload),
        file_name="atlas_ai_payload.json",
        mime="application/json",
    )

    with st.expander("Raw Atlas AI Payload", expanded=False):
        st.json(safe_payload)


def build_safe_payload(payload: dict) -> dict:
    """Build circular-safe Atlas AI payload."""
    return {
        "success": payload.get("success"),
        "version": payload.get("version"),
        "scope": payload.get("scope"),
        "profile_key": payload.get("profile_key"),
        "profile_a": payload.get("profile_a"),
        "profile_b": payload.get("profile_b"),
        "services_requested": payload.get("services_requested", []),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "metrics": payload.get("metrics", {}),
        "synthesis": payload.get("data", {}).get("synthesis", {}),
        "service_keys": sorted(
            list((payload.get("data", {}).get("services") or {}).keys())
        ),
    }


def format_confidence(record: dict) -> str:
    """Format confidence record."""
    if not isinstance(record, dict):
        return "n/a"

    return f"{record.get('percent', 0)}% {record.get('label', 'unknown')}"