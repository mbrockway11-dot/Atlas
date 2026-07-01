from __future__ import annotations

import streamlit as st

from atlas.services.profile_library_service import (
    list_profile_library_profiles,
    load_profile_library_payload,
)


def render_profile_library_page() -> None:
    st.title("Profile Library")
    st.caption("Browse saved profile artifacts through the service layer.")

    profiles = list_profile_library_profiles()

    if not profiles:
        st.warning("No saved profiles found.")
        return

    selected = st.selectbox("Profile", profiles)

    payload = load_profile_library_payload(selected)

    if not payload.get("exists"):
        st.error("Profile directory does not exist.")
        st.json(payload)
        return

    st.caption(payload.get("profile_dir", ""))

    available = payload.get("available", [])
    missing = payload.get("missing", [])

    col1, col2, col3 = st.columns(3)
    col1.metric("Available Files", len(available))
    col2.metric("Missing Files", len(missing))
    col3.metric("Profile Key", payload.get("profile_key", selected))

    if missing:
        st.warning("Missing files: " + ", ".join(missing))

    tabs = st.tabs(
        [
            "Interpretation",
            "ACF",
            "Intake",
            "Research Session",
            "Raw Payload",
        ]
    )

    with tabs[0]:
        interpretation = payload.get("interpretation")
        if interpretation is None:
            st.info("No profile interpretation file exists for this profile yet.")
        else:
            st.json(interpretation)

    with tabs[1]:
        acf = payload.get("acf")
        if acf is None:
            st.info("No ACF profile exists for this profile yet.")
        else:
            st.json(acf)

    with tabs[2]:
        intake = payload.get("intake")
        if intake is None:
            st.info("No intake metadata exists for this profile yet.")
        else:
            st.json(intake)

    with tabs[3]:
        research_session = payload.get("research_session")
        if research_session is None:
            st.info("No research session exists for this profile yet.")
        else:
            st.json(research_session)

    with tabs[4]:
        st.json(payload)
