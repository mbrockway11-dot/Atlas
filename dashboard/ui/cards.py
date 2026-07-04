"""Reusable Atlas dashboard cards."""

from __future__ import annotations

from typing import Any

import streamlit as st


def atlas_card(
    title: str,
    body: str | None = None,
    *,
    subtitle: str | None = None,
    badge: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Render a standard Atlas card."""
    with st.container(border=True):
        top = st.columns([4, 1])

        with top[0]:
            st.subheader(title)
            if subtitle:
                st.caption(subtitle)

        with top[1]:
            if badge:
                st.markdown(f"**{badge}**")

        if body:
            st.markdown(body)

        if metadata:
            cols = st.columns(min(len(metadata), 4))
            for index, (key, value) in enumerate(metadata.items()):
                cols[index % len(cols)].metric(str(key), value)


def executive_summary_card(
    *,
    title: str,
    role: str = "",
    civilization_role: str = "",
    confidence: str = "",
    summary: str = "",
) -> None:
    """Render a profile-style executive summary card."""
    metadata = {}

    if role:
        metadata["Role"] = role

    if civilization_role:
        metadata["Function"] = civilization_role

    if confidence:
        metadata["Confidence"] = confidence

    atlas_card(
        title=title,
        subtitle="Executive Summary",
        body=summary,
        badge=role or None,
        metadata=metadata,
    )


def interpretation_card(
    *,
    title: str = "Human Interpretation",
    interpretation: str,
) -> None:
    """Render human interpretation text."""
    atlas_card(title, interpretation)


def evidence_card(
    *,
    evidence: list[str],
    title: str = "Evidence",
    expanded: bool = False,
) -> None:
    """Render evidence as a collapsible card."""
    with st.expander(title, expanded=expanded):
        if not evidence:
            st.info("No evidence surfaced.")
            return

        for item in evidence:
            st.markdown(f"- {item}")


def warning_card(
    *,
    warnings: list[str],
    title: str = "Cautions",
    expanded: bool = False,
) -> None:
    """Render warnings/cautions."""
    if not warnings:
        return

    with st.expander(title, expanded=expanded):
        for item in warnings:
            st.warning(item)


def raw_payload_card(
    *,
    payload: dict[str, Any],
    title: str = "Developer Payload",
    expanded: bool = False,
) -> None:
    """Render raw JSON for developer inspection."""
    with st.expander(title, expanded=expanded):
        st.json(payload)


def relationship_card(
    *,
    profile_a: str,
    profile_b: str,
    summary: str,
    dynamic: str = "",
    confidence: str = "",
) -> None:
    """Render relationship summary card."""
    metadata = {}

    if confidence:
        metadata["Confidence"] = confidence

    atlas_card(
        title=f"{profile_a} ? {profile_b}",
        subtitle="Relationship Intelligence",
        body=f"{summary}\n\n{dynamic}".strip(),
        badge="Relationship",
        metadata=metadata,
    )


def temporal_card(
    *,
    title: str = "Temporal Intelligence",
    summary: str,
    date_window: str = "",
    confidence: str = "",
) -> None:
    """Render temporal summary card."""
    metadata = {}

    if date_window:
        metadata["Window"] = date_window

    if confidence:
        metadata["Confidence"] = confidence

    atlas_card(
        title=title,
        subtitle="Timing / Activation",
        body=summary,
        badge="Temporal",
        metadata=metadata,
    )


def metric_row(metrics: dict[str, Any]) -> None:
    """Render a standard row of metrics."""
    if not metrics:
        return

    cols = st.columns(min(len(metrics), 4))

    for index, (key, value) in enumerate(metrics.items()):
        cols[index % len(cols)].metric(str(key), value)
