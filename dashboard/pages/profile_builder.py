"""Profile Builder page."""

from __future__ import annotations

import streamlit as st

from atlas.acf.builder import build_acf_profile, export_acf_profile
from atlas.database import upsert_entity
from atlas.essence.profile import build_essence_profile
from atlas.interpretation.profile import (
    interpret_profile_summary,
    profile_interpretation_to_dict,
)
from atlas.library.profile_library import (
    LIBRARY_DIR,
    save_profile_to_library,
    safe_name,
)
from atlas.profiles.summary import build_individual_profile_summary
from atlas.reports.markdown import build_profile_markdown_report, write_markdown_report
from components.functional_role_panel import render_functional_role_panel
from utils.io import write_json


def render_profile_builder_page() -> None:
    """Render Profile Builder page."""
    st.header("Build Profile")

    name = st.text_input("Name", placeholder="Gaius Julius Caesar")

    col1, col2 = st.columns(2)

    with col1:
        entity_type = st.selectbox(
            "Entity Type",
            ["person", "institution", "civilization", "organization", "cohort"],
        )

    with col2:
        birth_confidence = st.selectbox(
            "Birth Confidence",
            ["unknown", "low", "medium", "high"],
        )

    tags_raw = st.text_input("Tags", placeholder="rome, military, founder")
    notes = st.text_area(
        "Notes",
        placeholder="Optional research notes or source comments.",
    )

    col3, col4 = st.columns(2)

    with col3:
        save_library = st.checkbox("Save to profile library", value=True)

    with col4:
        build_acf = st.checkbox("Export ACF", value=True)

    if st.button("Build Atlas Profile", type="primary"):
        if not name.strip():
            st.error("Enter a name first.")
            return

        tags = [
            tag.strip()
            for tag in tags_raw.split(",")
            if tag.strip()
        ]

        profile_key = safe_name(name)
        profile_dir = LIBRARY_DIR / profile_key

        with st.spinner("Building profile..."):
            if save_library:
                profile_dir = save_profile_to_library(name)
            else:
                profile_dir.mkdir(parents=True, exist_ok=True)

            summary = build_individual_profile_summary(name)
            interpretation = interpret_profile_summary(summary)
            report = build_profile_markdown_report(summary, interpretation)

            summary_path = profile_dir / "profile_summary.json"
            interpretation_path = profile_dir / "profile_interpretation.json"
            report_path = profile_dir / "codex_report.md"

            write_json(summary_path, summary)
            write_json(
                interpretation_path,
                profile_interpretation_to_dict(interpretation),
            )
            write_markdown_report(report, report_path)

            essence_paths = build_essence_profile(name, profile_dir)

            acf = build_acf_profile(
                name=name,
                entity_type=entity_type,
            )

            if build_acf:
                acf_path = profile_dir / "profile.acf.json"
                export_acf_profile(
                    name=name,
                    output_path=acf_path,
                    entity_type=entity_type,
                )

            entity = upsert_entity(
                name=name,
                entity_type=entity_type,
                tags=tags,
                birth_confidence=birth_confidence,
                notes=notes or None,
            )

        st.success("Profile built and indexed successfully.")
        st.write(f"Entity ID: `{entity['id']}`")
        st.write(f"Profile folder: `{profile_dir}`")
        st.write(f"Essence graph: `{essence_paths['json']}`")
        st.write(f"Essence 3D SVG: `{essence_paths['svg']}`")

        st.subheader("Summary")
        for line in interpretation.summary_lines:
            st.write(f"- {line}")

        render_functional_role_panel(acf)

        render_legacy_classification_debug(acf)


def render_legacy_classification_debug(acf: dict) -> None:
    """Render legacy classification only as collapsed debug output."""
    with st.expander("Legacy Classification Debug"):
        st.warning(
            "This is Atlas v1 legacy classification from acf['essence']. "
            "Atlas v2 Functional Role above is the canonical classification."
        )
        st.json(acf.get("essence", {}).get("classification", {}))
