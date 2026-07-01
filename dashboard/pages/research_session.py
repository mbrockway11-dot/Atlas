"""Research Session dashboard page.

This page is service-backed. Dashboard code renders controls, summaries, and
JSON views only. Research session construction is routed through
atlas.services.research_session_service.
"""

from __future__ import annotations

import json

import streamlit as st

from atlas.services.profile_service import list_profile_keys, resolve_profile_display_name
from atlas.services.research_session_service import get_research_session


def render_research_session_page() -> None:
    """Render Research Session dashboard."""
    st.header("Research Session")
    st.caption(
        "Build and inspect the canonical Atlas research session for a saved profile."
    )

    profile_keys = list_profile_keys()

    if not profile_keys:
        st.error("No saved profiles found in the profile library.")
        return

    selected_profile = st.selectbox(
        "Profile",
        profile_keys,
        format_func=resolve_profile_display_name,
    )

    transit_date = st.text_input("Transit date", value="2026-06-29")

    try:
        session = get_research_session(
            selected_profile,
            transit_date=transit_date,
        )
    except Exception as exc:
        st.error("Research session service failed.")
        st.exception(exc)
        return

    render_summary(selected_profile, session)

    tab_overview, tab_identity, tab_temporal, tab_raw, tab_export = st.tabs(
        [
            "Overview",
            "Identity",
            "Temporal",
            "Raw Session",
            "Export",
        ]
    )

    with tab_overview:
        render_overview(session)

    with tab_identity:
        render_identity(session)

    with tab_temporal:
        render_temporal(session)

    with tab_raw:
        st.json(session)

    with tab_export:
        render_export(selected_profile, session)


def render_summary(profile_key: str, session: object) -> None:
    """Render top-level session summary."""
    st.subheader(resolve_profile_display_name(profile_key))

    if isinstance(session, dict):
        c1, c2, c3 = st.columns(3)
        c1.metric("Top-level keys", len(session.keys()))
        c2.metric("Has identity", "yes" if "identity" in session else "no")
        c3.metric("Has temporal", "yes" if has_temporal_data(session) else "no")
    else:
        st.info(f"Session object type: {type(session).__name__}")


def render_overview(session: object) -> None:
    """Render overview of research session."""
    st.markdown("## Overview")

    if not isinstance(session, dict):
        st.json(session)
        return

    rows = []
    for key, value in session.items():
        rows.append(
            {
                "section": key,
                "type": type(value).__name__,
                "items": len(value) if hasattr(value, "__len__") else None,
            }
        )

    st.dataframe(rows, width="stretch")


def render_identity(session: object) -> None:
    """Render identity-related section."""
    st.markdown("## Identity")

    if not isinstance(session, dict):
        st.info("Session is not dictionary-like.")
        return

    identity = session.get("identity")
    if identity is None:
        st.info("No identity section found.")
        return

    st.json(identity)


def render_temporal(session: object) -> None:
    """Render temporal-related session data."""
    st.markdown("## Temporal")

    if not isinstance(session, dict):
        st.info("Session is not dictionary-like.")
        return

    temporal_keys = [
        "temporal",
        "temporal_payload",
        "temporal_intelligence",
        "birth",
        "natal",
        "transits",
        "dasha",
    ]

    found = {
        key: session[key]
        for key in temporal_keys
        if key in session
    }

    identity = session.get("identity")
    if isinstance(identity, dict):
        for key in temporal_keys:
            if key in identity:
                found[f"identity.{key}"] = identity[key]

    if not found:
        st.info("No known temporal section found in this research session.")
        st.caption(f"Available keys: {sorted(session.keys())}")
        return

    st.json(found)


def render_export(profile_key: str, session: object) -> None:
    """Render export controls."""
    st.markdown("## Export")

    payload = json.dumps(
        session,
        indent=2,
        sort_keys=True,
        default=str,
    )

    st.download_button(
        "Download research_session.json",
        data=payload,
        file_name=f"{profile_key}_research_session.json",
        mime="application/json",
    )


def has_temporal_data(session: dict) -> bool:
    """Return whether session appears to contain temporal data."""
    temporal_keys = {
        "temporal",
        "temporal_payload",
        "temporal_intelligence",
        "birth",
        "natal",
        "transits",
        "dasha",
    }

    if any(key in session for key in temporal_keys):
        return True

    identity = session.get("identity")
    if isinstance(identity, dict):
        return any(key in identity for key in temporal_keys)

    return False
