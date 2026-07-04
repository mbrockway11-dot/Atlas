"""Atlas temporal timeline UI components."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.cards import atlas_card
from dashboard.ui.metrics import confidence_meter


def render_timeline(
    events: list[dict[str, Any]],
    *,
    title: str = "Temporal Timeline",
    subtitle: str = "Activation sequence",
) -> None:
    """Render a simple temporal event timeline."""
    atlas_card(
        title=title,
        subtitle=subtitle,
        body="Temporal intelligence is shown as ordered activation windows.",
        badge="Timeline",
    )

    if not events:
        st.info("No temporal events available.")
        return

    for event in events:
        render_timeline_event(event)


def render_timeline_event(event: dict[str, Any]) -> None:
    """Render one timeline event."""
    label = event.get("label") or event.get("title") or "Temporal Event"
    date = event.get("date") or event.get("window") or event.get("timeframe") or "unspecified"
    summary = event.get("summary") or event.get("description") or ""
    intensity = event.get("intensity")
    confidence = event.get("confidence", "")

    with st.container(border=True):
        st.markdown(f"### {label}")
        st.caption(str(date))

        if summary:
            st.markdown(summary)

        cols = st.columns(2)

        if intensity is not None:
            with cols[0]:
                confidence_meter("Activation", intensity)

        if confidence:
            with cols[1]:
                st.metric("Confidence", confidence)


def render_phase_timeline(
    phases: list[dict[str, Any]],
    *,
    title: str = "Temporal Phases",
) -> None:
    """Render phase-based timeline."""
    st.subheader(title)

    if not phases:
        st.info("No temporal phases available.")
        return

    for index, phase in enumerate(phases, start=1):
        label = phase.get("label") or phase.get("title") or f"Phase {index}"
        window = phase.get("window") or phase.get("date_window") or "unspecified"
        tone = phase.get("tone") or phase.get("theme") or ""
        behavior = phase.get("behavior") or phase.get("probable_behavior") or ""

        with st.expander(f"{index}. {label} ? {window}", expanded=index == 1):
            if tone:
                st.markdown(f"**Theme:** {tone}")
            if behavior:
                st.markdown(behavior)

            intensity = phase.get("intensity")
            if intensity is not None:
                confidence_meter("Activation", intensity)


def build_default_forecast_phases(
    *,
    subject: str,
    date_window: str = "next 6 months",
) -> list[dict[str, Any]]:
    """Build placeholder forecast phases until deterministic phase data exists."""
    return [
        {
            "label": "Phase 1",
            "window": f"Opening of {date_window}",
            "tone": "Baseline activation",
            "behavior": (
                f"{subject} begins the window by expressing their default structural pattern more visibly."
            ),
            "intensity": 45,
        },
        {
            "label": "Phase 2",
            "window": f"Middle of {date_window}",
            "tone": "Pressure and differentiation",
            "behavior": (
                "The main stress pattern becomes easier to observe. Productive outcomes depend on whether "
                "the activated pattern is named and directed consciously."
            ),
            "intensity": 65,
        },
        {
            "label": "Phase 3",
            "window": f"Close of {date_window}",
            "tone": "Integration or repetition",
            "behavior": (
                "The system either integrates the pressure into a clearer role or repeats the old response pattern."
            ),
            "intensity": 55,
        },
    ]


def render_temporal_outlook(
    *,
    subject: str,
    date_window: str = "next 6 months",
    summary: str = "",
    phases: list[dict[str, Any]] | None = None,
    confidence: str = "",
) -> None:
    """Render a full temporal outlook card plus phase timeline."""
    atlas_card(
        title=f"{subject} Temporal Outlook",
        subtitle=date_window,
        body=summary or "Temporal outlook describes how the baseline structure becomes active over time.",
        badge="Temporal",
        metadata={"Confidence": confidence} if confidence else None,
    )

    render_phase_timeline(
        phases or build_default_forecast_phases(subject=subject, date_window=date_window),
        title="Forecast Phases",
    )
