
"""Identity section for Atlas dossiers."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.layout import divider
from dashboard.ui.metrics import metric_grid


def render_identity_section(profile: dict[str, Any]) -> None:
    """Render canonical identity information."""

    divider("Identity")

    identity = profile.get("identity", {})
    birth = profile.get("birth", {})
    lifecycle = profile.get("lifecycle", {})
    diagnostics = profile.get("diagnostics", {})

    if not isinstance(identity, dict):
        identity = {}

    if not isinstance(birth, dict):
        birth = {}

    if not isinstance(lifecycle, dict):
        lifecycle = {}

    metric_grid(
        {
            "Full Name": identity.get("full_name") or identity.get("display_name") or profile.get("name", "Unknown"),
            "Profile Key": identity.get("profile_key") or profile.get("profile_key", "Unknown"),
            "Birth Date": birth.get("date", "Missing"),
            "Birth Time": birth.get("time", "Missing"),
            "Birth Place": birth.get("place", "Missing"),
            "Lifecycle": lifecycle.get("status", "Unknown"),
        }
    )

    render_identity_summary(identity, birth, lifecycle, diagnostics)


def render_identity_summary(
    identity: dict[str, Any],
    birth: dict[str, Any],
    lifecycle: dict[str, Any],
    diagnostics: dict[str, Any],
) -> None:
    """Render readable identity summary."""

    st.markdown("### Identity Context")

    name = identity.get("full_name") or identity.get("display_name") or "This profile"
    profile_key = identity.get("profile_key", "unknown")
    birth_date = birth.get("date", "unknown date")
    birth_time = birth.get("time", "unknown time")
    birth_place = birth.get("place", "unknown place")
    lifecycle_status = lifecycle.get("status", "unknown lifecycle")
    compiler = diagnostics.get("compiler", "canonical compiler")

    st.markdown(
        f"""
**{name}** is stored in Atlas under the canonical profile key
`{profile_key}`.

The temporal layer is anchored to the recorded birth data:

- **Date:** {birth_date}
- **Time:** {birth_time}
- **Place:** {birth_place}

Lifecycle status is currently **{lifecycle_status}**.

This identity block is the factual anchor for all later Atlas layers, including cipher generation, Kamea projection, temporal compilation, graph construction, topology, resonance, classification, and semantic interpretation.
"""
    )

    if diagnostics:
        st.caption(f"Compiled by: {compiler}")


def extract_identity_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return identity payload from canonical profile."""
    return payload.get("identity", {}) if isinstance(payload.get("identity"), dict) else {}

