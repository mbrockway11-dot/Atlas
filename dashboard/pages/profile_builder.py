"""Profile Builder page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.structural_codex import render_structural_codex
from atlas.services.person_intake_service import create_person_profile
from atlas.services.profile_compile_service import compile_person_profile


def render_profile_builder_page() -> None:
    """Render Profile Builder."""
    st.title("Profile Builder")
    st.caption("Create a new Atlas profile intake record.")

    with st.form("person_intake_form"):
        full_name = st.text_input("Full name", placeholder="Nikola Tesla")
        birth_date = st.text_input("Birth date", placeholder="1856-07-10")
        birth_time = st.text_input("Birth time", placeholder="00:00")
        birth_place = st.text_input("Birth place", placeholder="Smiljan, Croatia")

        st.markdown("### Lifecycle")
        death_date = st.text_input("Death date", placeholder="1943-01-07 or leave blank if living/open")
        death_place = st.text_input("Death place", placeholder="New York City or leave blank")

        major_events_raw = st.text_area(
            "Major events",
            placeholder="One per line, format: YYYY-MM-DD | Label | Summary",
        )

        notes = st.text_area("Notes", placeholder="Optional context, source notes, or uncertainty.")
        overwrite = st.checkbox("Overwrite existing intake file", value=False)

        submitted = st.form_submit_button("Create Profile", type="primary")

    if not submitted:
        st.info("Enter a person and create a profile.intake.json record.")
        return

    payload = create_person_profile(
        full_name=full_name,
        birth_date=birth_date,
        birth_time=birth_time,
        birth_place=birth_place,
        death_date=death_date,
        death_place=death_place,
        major_events=parse_major_events(major_events_raw),
        notes=notes,
        overwrite=overwrite,
    )

    if not payload.get("success"):
        st.error("Profile intake was not created.")
        for error in payload.get("errors", []):
            st.error(error)
        for warning in payload.get("warnings", []):
            st.warning(warning)
        st.json(payload)
        return

    st.success(f"Created profile: {payload.get('profile_key')}")

    c1, c2 = st.columns(2)
    c1.metric("Profile Key", payload.get("profile_key", ""))
    c2.metric("Created Files", len(payload.get("created_files", [])))

    st.subheader("Created Files")
    for item in payload.get("created_files", []):
        st.code(item)

    warnings = payload.get("warnings", [])
    if warnings:
        st.subheader("Warnings")
        for warning in warnings:
            st.warning(warning)

    st.subheader("Compile Profile")

    compile_now = st.button(
        "Compile Profile",
        type="primary",
        key=f"compile_{payload.get('profile_key', '')}",
    )

    if compile_now:
        with st.spinner("Compiling Atlas profile..."):
            compile_payload = compile_person_profile(
                payload.get("profile_key", ""),
                force=True,
            )

        if compile_payload.get("success"):
            st.success("Profile compiled successfully.")

            st.subheader("Compiled Artifacts")
            for item in compile_payload.get("created_files", []):
                st.code(item)

            st.subheader("Artifact Status")
            st.json(compile_payload.get("artifact_status", {}))

            codex = compile_payload.get("structural_codex", {})
            if codex.get("success"):
                render_structural_codex(codex)
        else:
            st.error("Profile compile failed.")

        for warning in compile_payload.get("warnings", []):
            st.warning(warning)

        for error in compile_payload.get("errors", []):
            st.error(error)

        with st.expander("Raw Compile Payload", expanded=False):
            st.json(compile_payload)

    st.subheader("Next Steps")
    for step in payload.get("next_steps", []):
        st.markdown(f"- {step}")

    with st.expander("Raw Intake Payload", expanded=False):
        st.json(payload.get("intake", {}))

    with st.expander("Raw Service Payload", expanded=False):
        st.json(payload)


def render() -> None:
    """Backward-compatible render alias."""
    render_profile_builder_page()


if __name__ == "__main__":
    render_profile_builder_page()


def parse_major_events(raw: str) -> list[dict]:
    """Parse major event textarea into event records."""
    events: list[dict] = []

    for line in raw.splitlines():
        clean = line.strip()
        if not clean:
            continue

        parts = [part.strip() for part in clean.split("|")]

        events.append(
            {
                "date": parts[0] if len(parts) > 0 else "",
                "label": parts[1] if len(parts) > 1 else "Major Event",
                "summary": parts[2] if len(parts) > 2 else "",
            }
        )

    return events
