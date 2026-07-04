"""Reusable dossier UI components."""

from __future__ import annotations

from typing import Any

import streamlit as st


def dossier_section(title: str, subtitle: str = "") -> None:
    """Render a dossier section header."""
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)


def status_badge(label: str, status: str) -> None:
    """Render a status badge."""
    normalized = str(status or "unknown").lower()

    if normalized in {"compiled", "healthy", "success", "complete", "online"}:
        st.success(f"{label}: {status}")
    elif normalized in {"missing", "warning", "partial", "degraded"}:
        st.warning(f"{label}: {status}")
    elif normalized in {"error", "failed", "offline"}:
        st.error(f"{label}: {status}")
    else:
        st.info(f"{label}: {status}")


def confidence_label(confidence: Any) -> str:
    """Format confidence object."""
    if isinstance(confidence, dict):
        percent = confidence.get("percent")
        label = confidence.get("label", "unknown")
        if percent is not None:
            return f"{percent}% {label}"
        return str(label)

    return str(confidence or "unknown")


def key_value_grid(values: dict[str, Any], columns: int = 3) -> None:
    """Render key values as Streamlit metrics."""
    clean_items = [
        (humanize(str(key)), format_value(value))
        for key, value in values.items()
        if is_simple(value)
    ]

    if not clean_items:
        return

    cols = st.columns(columns)

    for index, (key, value) in enumerate(clean_items):
        cols[index % columns].metric(key, value)


def narrative_card(title: str, body: str, subtitle: str = "") -> None:
    """Render a narrative card."""
    if not body:
        return

    with st.container(border=True):
        st.markdown(f"### {title}")
        if subtitle:
            st.caption(subtitle)
        st.markdown(body)


def data_expander(title: str, data: Any, expanded: bool = False) -> None:
    """Render JSON data in an expander."""
    if not data:
        return

    with st.expander(title, expanded=expanded):
        st.json(data)


def is_simple(value: Any) -> bool:
    """Return whether a value can be shown as a metric."""
    return isinstance(value, (str, int, float, bool)) or value is None


def format_value(value: Any) -> str:
    """Format a value for display."""
    if value is None or value == "":
        return "n/a"
    if isinstance(value, bool):
        return "True" if value else "False"
    return str(value)


def humanize(value: str) -> str:
    """Humanize keys."""
    replacements = {
        "cig": "CIG",
        "stg": "STG",
        "id": "ID",
        "ai": "AI",
    }

    parts = str(value).replace("_", " ").split()
    return " ".join(replacements.get(part.lower(), part.title()) for part in parts)
