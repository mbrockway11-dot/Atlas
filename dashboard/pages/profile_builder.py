"""Service-backed Profile Builder dashboard page."""

from __future__ import annotations

from typing import Any

import streamlit as st

from atlas.services.profile_builder_service import ProfileBuilderPayload, build_profile_builder_payload
from components.functional_role_panel import render_functional_role_panel


ENTITY_TYPES = [
    "person",
    "institution",
    "civilization",
    "organization",
    "cohort",
]

BIRTH_CONFIDENCE_LEVELS = [
    "unknown",
    "low",
    "medium",
    "high",
]


def render_profile_builder_page() -> None:
    """Render the Profile Builder as a thin UI layer over the service."""
    st.header("Build Profile")
    st.caption("Create, compile, index, and optionally export an Atlas profile.")

    form_state = render_profile_builder_form()
    if form_state is None:
        return

    with st.spinner("Building profile..."):
        payload = build_profile_builder_payload(**form_state)

    render_profile_builder_payload(payload)


def render_profile_builder_form() -> dict[str, Any] | None:
    """Render Profile Builder inputs and return normalized service args on submit."""
    with st.form("profile_builder_form"):
        name = st.text_input("Name", placeholder="Gaius Julius Caesar")

        col1, col2 = st.columns(2)
        with col1:
            entity_type = st.selectbox("Entity Type", ENTITY_TYPES)
        with col2:
            birth_confidence = st.selectbox("Birth Confidence", BIRTH_CONFIDENCE_LEVELS)

        tags_raw = st.text_input("Tags", placeholder="rome, military, founder")
        notes = st.text_area(
            "Notes",
            placeholder="Optional research notes or source comments.",
        )

        col3, col4 = st.columns(2)
        with col3:
            save_library = st.checkbox("Save to profile library", value=True)
        with col4:
            export_acf = st.checkbox("Export ACF", value=True)

        submitted = st.form_submit_button("Build Atlas Profile", type="primary")

    if not submitted:
        return None

    return {
        "name": name,
        "entity_type": entity_type,
        "birth_confidence": birth_confidence,
        "tags": parse_tags(tags_raw),
        "notes": notes,
        "save_library": save_library,
        "export_acf": export_acf,
    }


def parse_tags(tags_raw: str) -> list[str]:
    """Normalize comma-separated tags from the UI."""
    return [tag.strip() for tag in tags_raw.split(",") if tag.strip()]


def render_profile_builder_payload(payload: ProfileBuilderPayload) -> None:
    """Render the canonical Profile Builder service payload."""
    if not payload.success:
        st.error("\n".join(payload.errors))
        return

    st.success("Profile built and indexed successfully.")
    render_profile_metadata(payload)
    render_profile_summary(payload)

    if payload.acf:
        render_functional_role_panel(payload.acf)
        render_legacy_classification_debug(payload.acf)

    if payload.warnings:
        render_profile_warnings(payload.warnings)


def render_profile_metadata(payload: ProfileBuilderPayload) -> None:
    """Render profile identity and artifact paths returned by the service."""
    st.subheader("Generated Artifacts")

    if payload.entity:
        st.write(f"Entity ID: `{payload.entity['id']}`")

    path_labels = {
        "profile_dir": "Profile folder",
        "summary": "Summary JSON",
        "interpretation": "Interpretation JSON",
        "report": "Markdown report",
        "essence_json": "Essence graph",
        "essence_svg": "Essence 3D SVG",
        "acf": "ACF export",
    }

    for key, label in path_labels.items():
        path = payload.paths.get(key)
        if path:
            st.write(f"{label}: `{path}`")


def render_profile_summary(payload: ProfileBuilderPayload) -> None:
    """Render interpretation summary lines returned by the service."""
    if not payload.interpretation:
        return

    st.subheader("Summary")
    for line in payload.interpretation.summary_lines:
        st.write(f"- {line}")


def render_profile_warnings(warnings: list[str]) -> None:
    """Render non-fatal Profile Builder service warnings."""
    with st.expander("Profile build warnings"):
        for warning in warnings:
            st.warning(warning)


def render_legacy_classification_debug(acf: dict[str, Any]) -> None:
    """Render legacy classification only as collapsed debug output."""
    with st.expander("Legacy Classification Debug"):
        st.warning(
            "This is Atlas v1 legacy classification from acf['essence']. "
            "Atlas v2 Functional Role above is the canonical classification."
        )
        st.json(acf.get("essence", {}).get("classification", {}))
