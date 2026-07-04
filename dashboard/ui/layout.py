"""Atlas dashboard layout helpers."""

from __future__ import annotations

from typing import Any

import streamlit as st


def atlas_page(
    *,
    title: str,
    subtitle: str = "",
    status: str = "",
) -> None:
    """Render a standard Atlas page header."""
    st.title(title)

    if subtitle:
        st.caption(subtitle)

    if status:
        st.markdown(f"**Status:** {status}")


def hero_panel(
    *,
    title: str,
    subtitle: str = "",
    body: str = "",
    metrics: dict[str, Any] | None = None,
) -> None:
    """Render a hero-style panel."""
    with st.container(border=True):
        st.header(title)

        if subtitle:
            st.caption(subtitle)

        if body:
            st.markdown(body)

        if metrics:
            cols = st.columns(min(len(metrics), 4))
            for index, (label, value) in enumerate(metrics.items()):
                cols[index % len(cols)].metric(str(label), value)


def two_column_layout(
    *,
    left_title: str,
    right_title: str,
    left_width: int = 2,
    right_width: int = 1,
):
    """Return two named Streamlit columns."""
    left, right = st.columns([left_width, right_width])

    with left:
        st.subheader(left_title)

    with right:
        st.subheader(right_title)

    return left, right


def report_layout(
    *,
    summary_title: str = "Executive Summary",
    details_title: str = "Details",
):
    """Return summary/detail report columns."""
    return two_column_layout(
        left_title=summary_title,
        right_title=details_title,
        left_width=2,
        right_width=1,
    )


def developer_panel(
    payload: dict[str, Any],
    *,
    title: str = "Developer Payload",
    expanded: bool = False,
) -> None:
    """Render a standard developer JSON panel."""
    with st.expander(title, expanded=expanded):
        st.json(payload)


def divider(label: str = "") -> None:
    """Render a visual divider with optional label."""
    if label:
        st.markdown(f"---\n### {label}")
    else:
        st.divider()


def action_row(actions: dict[str, bool]) -> dict[str, bool]:
    """Render a row of action buttons and return clicked states."""
    if not actions:
        return {}

    cols = st.columns(len(actions))
    result: dict[str, bool] = {}

    for index, (label, primary) in enumerate(actions.items()):
        result[label] = cols[index].button(
            label,
            type="primary" if primary else "secondary",
        )

    return result
