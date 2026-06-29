"""Research Session dashboard page."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from atlas.research.session import (
    build_research_session,
    research_session_to_dict,
)


DEFAULT_PROFILE_DIR = Path("output/library/profiles")


def render_research_session_page() -> None:
    """Render Research Session page."""
    st.header("Research Session")
    st.caption("Build a complete AtlasIdentity → Interpretation → Report session.")

    root = Path(
        st.text_input(
            "Profile library directory",
            value=str(DEFAULT_PROFILE_DIR),
        )
    )

    if not root.exists():
        st.error(f"Profile directory not found: {root}")
        return

    profiles = load_profiles(root)

    if not profiles:
        st.warning("No profiles found.")
        return

    selected_name = st.selectbox(
        "Select profile",
        [profile["name"] for profile in profiles],
    )

    selected = next(
        profile
        for profile in profiles
        if profile["name"] == selected_name
    )

    transit_date = st.text_input(
        "Transit date",
        value="2026-06-29",
        help="Use YYYY-MM-DD.",
    )

    profile_path = root / selected["slug"]

    if st.button("Build Research Session"):
        with st.spinner("Building research session..."):
            session = build_research_session(
                profile_path,
                transit_date=transit_date,
            )

        render_session_summary(session)
        render_report(session)
        render_exports(session)


def load_profiles(root: Path) -> list[dict]:
    """Load profile names and slugs."""
    profiles: list[dict] = []

    for profile_path in sorted(root.iterdir()):
        if not profile_path.is_dir():
            continue

        intake_path = profile_path / "profile.intake.json"
        name = profile_path.name

        if intake_path.exists():
            try:
                intake = json.loads(
                    intake_path.read_text(encoding="utf-8")
                )
                name = intake.get("name", name)
            except json.JSONDecodeError:
                pass

        profiles.append(
            {
                "name": name,
                "slug": profile_path.name,
            }
        )

    return profiles


def render_session_summary(session) -> None:
    """Render session summary."""
    st.markdown("## Session Summary")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Name", session.name)
    c2.metric("Version", session.version)
    c3.metric("Sections", session.summary.get("section_count", 0))
    c4.metric("Transit Date", session.transit_date or "Today")

    with st.expander("Session Summary JSON", expanded=False):
        st.json(session.summary)


def render_report(session) -> None:
    """Render Markdown report."""
    st.markdown("## Atlas Report")
    st.markdown(session.report.markdown)


def render_exports(session) -> None:
    """Render export buttons."""
    st.markdown("## Exports")

    session_json = json.dumps(
        research_session_to_dict(session),
        indent=2,
        sort_keys=True,
    )

    c1, c2 = st.columns(2)

    c1.download_button(
        label="Download Research Session JSON",
        data=session_json,
        file_name=f"{slugify(session.name)}_research_session.json",
        mime="application/json",
    )

    c2.download_button(
        label="Download Atlas Report Markdown",
        data=session.report.markdown,
        file_name=f"{slugify(session.name)}_atlas_report.md",
        mime="text/markdown",
    )


def slugify(value: str) -> str:
    """Build safe filename slug."""
    return (
        value.casefold()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )