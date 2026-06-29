"""Profile Library page."""

from __future__ import annotations

import json

import streamlit as st

from atlas.acf.builder import export_acf_profile
from atlas.library.profile_library import (
    LIBRARY_DIR,
    list_saved_profiles,
    load_profile_interpretation,
)
from components.functional_role_panel import render_functional_role_panel
from utils.dataframe import dict_to_dataframe


def render_profile_library_page() -> None:
    """Render Profile Library page."""
    st.header("Profile Library")

    profiles = list_saved_profiles()

    if not profiles:
        st.info("No saved profiles yet.")
        return

    selected = st.selectbox("Saved profiles", profiles)

    if not selected:
        return

    interpretation = load_profile_interpretation(selected)
    acf = load_or_repair_acf(selected, interpretation["name"])

    st.subheader(interpretation["name"])
    st.write(f"Analysis count: `{interpretation['analysis_count']}`")

    if acf is not None:
        render_functional_role_panel(acf)
    else:
        st.warning("No ACF available. Rebuild this profile to enable Atlas v2 role analysis.")

    st.markdown("### Summary")
    for line in interpretation["summary_lines"]:
        st.write(f"- {line}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Dominant Patterns")
        st.dataframe(
            dict_to_dataframe(interpretation["dominant_patterns"], "pattern", "count"),
            width="stretch",
        )

    with col2:
        st.markdown("### Dominant Motifs")
        st.dataframe(
            dict_to_dataframe(interpretation["dominant_motifs"], "motif", "count"),
            width="stretch",
        )

    profile_dir = LIBRARY_DIR / selected
    report_path = profile_dir / "codex_report.md"
    essence_svg = profile_dir / f"{selected}_essence_topology_3d.svg"
    acf_path = profile_dir / "profile.acf.json"

    st.markdown("### Files")
    st.write(f"Folder: `{profile_dir}`")
    st.write(f"Codex report: `{report_path}`")
    st.write(f"Essence SVG: `{essence_svg}`")
    st.write(f"ACF: `{acf_path}`")

    if report_path.exists():
        with st.expander("View Codex Report"):
            st.markdown(report_path.read_text(encoding="utf-8"))

    if acf is not None:
        render_legacy_library_debug(acf)


def load_or_repair_acf(profile_key: str, name: str) -> dict | None:
    """Load ACF and repair/export it if missing or stale."""
    profile_dir = LIBRARY_DIR / profile_key
    acf_path = profile_dir / "profile.acf.json"

    if not acf_path.exists():
        profile_dir.mkdir(parents=True, exist_ok=True)
        export_acf_profile(
            name=name,
            output_path=acf_path,
            entity_type="person",
        )

    if not acf_path.exists():
        return None

    data = json.loads(acf_path.read_text(encoding="utf-8"))

    required_keys = {
        "identity",
        "identity_graph",
        "identity_persistence",
        "invariant_analysis",
    }

    if required_keys.issubset(data.keys()):
        return data

    entity_type = data.get("identity", {}).get("entity_type", "person")

    export_acf_profile(
        name=name,
        output_path=acf_path,
        entity_type=entity_type,
    )

    return json.loads(acf_path.read_text(encoding="utf-8"))


def render_legacy_library_debug(acf: dict) -> None:
    """Render legacy library classification only as collapsed debug."""
    with st.expander("Legacy Classification Debug"):
        st.warning(
            "This is Atlas v1 legacy classification from acf['essence']. "
            "Atlas v2 Functional Role above is the canonical classification."
        )
        st.json(acf.get("essence", {}).get("classification", {}))