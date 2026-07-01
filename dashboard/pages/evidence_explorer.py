"""Evidence Explorer dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.evidence_service import (
    build_profile_evidence_payload,
    build_relationship_evidence_payload,
    json_export,
    list_evidence_profiles,
)


def render_evidence_explorer_page() -> None:
    """Render Evidence Explorer dashboard."""
    st.header("Evidence Explorer")
    st.caption(
        "Inspect Atlas claims, confidence, evidence, cautions, and source traces."
    )

    profiles = list_evidence_profiles()

    if not profiles:
        st.warning("No saved profiles found.")
        return

    mode = st.radio(
        "Evidence scope",
        ["Profile", "Relationship"],
        horizontal=True,
    )

    if mode == "Profile":
        render_profile_mode(profiles)
    else:
        render_relationship_mode(profiles)


def render_profile_mode(profiles: list[str]) -> None:
    """Render profile evidence mode."""
    selected = st.selectbox(
        "Profile",
        profiles,
        key="evidence_profile",
    )

    if not st.button("Build Profile Evidence", type="primary"):
        st.info("Select a profile and build evidence records.")
        return

    with st.spinner("Building profile evidence..."):
        payload = build_profile_evidence_payload(selected)

    render_payload(payload)


def render_relationship_mode(profiles: list[str]) -> None:
    """Render relationship evidence mode."""
    col_a, col_b = st.columns(2)

    with col_a:
        profile_a = st.selectbox(
            "Profile A",
            profiles,
            index=0,
            key="evidence_profile_a",
        )

    with col_b:
        profile_b = st.selectbox(
            "Profile B",
            profiles,
            index=1 if len(profiles) > 1 else 0,
            key="evidence_profile_b",
        )

    if profile_a == profile_b:
        st.warning("Select two different profiles.")
        return

    if not st.button("Build Relationship Evidence", type="primary"):
        st.info("Select two profiles and build evidence records.")
        return

    with st.spinner("Building relationship evidence..."):
        payload = build_relationship_evidence_payload(profile_a, profile_b)

    render_payload(payload)


def render_payload(payload: dict) -> None:
    """Render evidence payload."""
    if not payload.get("success"):
        st.error("Evidence build failed.")
        for error in payload.get("errors", []):
            st.error(error)
        st.json(build_safe_payload(payload))
        return

    render_metrics(payload)
    render_warnings(payload)
    render_records(payload)
    render_markdown(payload)
    render_exports(payload)


def render_metrics(payload: dict) -> None:
    """Render evidence metrics."""
    st.markdown("## Evidence Health")

    metrics = payload.get("metrics", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Claims", metrics.get("claim_count", 0))
    c2.metric("Evidence Items", metrics.get("evidence_count", 0))
    c3.metric("Cautions", metrics.get("caution_count", 0))
    c4.metric(
        "Avg Confidence",
        f"{metrics.get('average_confidence_percent', 0)}%",
    )

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("High", metrics.get("high_confidence_claims", 0))
    c6.metric("Moderate", metrics.get("moderate_confidence_claims", 0))
    c7.metric("Limited", metrics.get("limited_confidence_claims", 0))
    c8.metric("Low", metrics.get("low_confidence_claims", 0))

    with st.expander("Raw Evidence Metrics", expanded=False):
        st.json(metrics)


def render_warnings(payload: dict) -> None:
    """Render warnings and errors."""
    for warning in payload.get("warnings", []):
        st.warning(warning)

    for error in payload.get("errors", []):
        st.error(error)


def render_records(payload: dict) -> None:
    """Render normalized evidence records."""
    st.markdown("## Evidence Records")

    records = payload.get("data", {}).get("records", [])

    if not records:
        st.info("No evidence records available.")
        return

    dataframe = build_records_dataframe(records)

    col_a, col_b = st.columns(2)

    with col_a:
        confidence_filter = st.multiselect(
            "Confidence labels",
            sorted(dataframe["confidence_label"].dropna().unique().tolist()),
            default=sorted(dataframe["confidence_label"].dropna().unique().tolist()),
        )

    with col_b:
        section_filter = st.multiselect(
            "Sections",
            sorted(dataframe["section"].dropna().unique().tolist()),
            default=sorted(dataframe["section"].dropna().unique().tolist()),
        )

    filtered = dataframe[
        dataframe["confidence_label"].isin(confidence_filter)
        & dataframe["section"].isin(section_filter)
    ]

    st.dataframe(filtered, width="stretch")

    st.download_button(
        "Download Evidence Records CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="atlas_evidence_records.csv",
        mime="text/csv",
    )

    st.markdown("## Claim Inspector")

    record_options = {
        f"{row['section']} | {row['confidence_label']} | {row['claim'][:80]}": row["id"]
        for _, row in filtered.iterrows()
    }

    if not record_options:
        st.info("No records match the selected filters.")
        return

    selected_label = st.selectbox(
        "Select claim",
        list(record_options.keys()),
    )

    selected_id = record_options[selected_label]
    selected_record = next(
        record for record in records if record.get("id") == selected_id
    )

    render_record_detail(selected_record)


def build_records_dataframe(records: list[dict]) -> pd.DataFrame:
    """Build evidence records dataframe."""
    return pd.DataFrame(
        [
            {
                "id": record.get("id"),
                "source_type": record.get("source_type"),
                "section": record.get("section"),
                "claim": record.get("claim"),
                "confidence_label": record.get("confidence_label"),
                "confidence_percent": record.get("confidence_percent"),
                "evidence_count": record.get("evidence_count"),
                "caution_count": record.get("caution_count"),
                "source_service": record.get("trace", {}).get("source_service"),
            }
            for record in records
        ]
    )


def render_record_detail(record: dict) -> None:
    """Render one evidence record."""
    st.markdown("### Claim")
    st.write(record.get("claim", ""))

    confidence = record.get("confidence", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Confidence", confidence.get("label", "unknown"))
    c2.metric("Percent", f"{confidence.get('percent', 0)}%")
    c3.metric("Evidence Items", record.get("evidence_count", 0))

    st.markdown("### Evidence")
    evidence = record.get("evidence", [])

    if evidence:
        for item in evidence:
            st.write(f"- {item}")
    else:
        st.info("No evidence items attached.")

    cautions = record.get("cautions", [])

    if cautions:
        st.markdown("### Cautions")
        for caution in cautions:
            st.warning(caution)

    st.markdown("### Trace")
    st.json(record.get("trace", {}))

    with st.expander("Raw Evidence Record", expanded=False):
        st.json(record)


def render_markdown(payload: dict) -> None:
    """Render evidence Markdown."""
    st.markdown("## Evidence Markdown")

    markdown = payload.get("exports", {}).get("markdown", "")

    if not markdown:
        st.info("No Markdown evidence report generated.")
        return

    with st.expander("View Markdown Report", expanded=False):
        st.markdown(markdown)


def render_exports(payload: dict) -> None:
    """Render evidence exports."""
    st.markdown("## Exports")

    safe_payload = build_safe_payload(payload)

    c1, c2, c3 = st.columns(3)

    c1.download_button(
        "Download Markdown",
        data=payload.get("exports", {}).get("markdown", ""),
        file_name="atlas_evidence_report.md",
        mime="text/markdown",
    )

    c2.download_button(
        "Download Evidence JSON",
        data=json_export(payload.get("exports", {}).get("evidence_json", [])),
        file_name="atlas_evidence_records.json",
        mime="application/json",
    )

    c3.download_button(
        "Download Full Payload JSON",
        data=json_export(safe_payload),
        file_name="atlas_evidence_payload.json",
        mime="application/json",
    )

    with st.expander("Raw Evidence Payload", expanded=False):
        st.json(safe_payload)


def build_safe_payload(payload: dict) -> dict:
    """Build circular-safe evidence payload."""
    return {
        "success": payload.get("success"),
        "version": payload.get("version"),
        "scope": payload.get("scope"),
        "profile_key": payload.get("profile_key"),
        "profile_a": payload.get("profile_a"),
        "profile_b": payload.get("profile_b"),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "metrics": payload.get("metrics", {}),
        "records": payload.get("data", {}).get("records", []),
        "source_summary": payload.get("data", {}).get("source_summary", {}),
    }
