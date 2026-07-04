"""Atlas UI badges."""

from __future__ import annotations

import streamlit as st


def status_badge(label: str, status: str = "neutral") -> None:
    """Render a small status badge."""
    icon = {
        "ok": "?",
        "healthy": "?",
        "warning": "??",
        "error": "?",
        "limited": "??",
        "neutral": "?",
    }.get(status.lower(), "?")

    st.markdown(f"{icon} **{label}**")


def confidence_badge(confidence: str) -> None:
    """Render confidence label."""
    status = "ok"
    if "limited" in confidence.lower() or "low" in confidence.lower():
        status = "limited"
    elif "error" in confidence.lower() or "none" in confidence.lower():
        status = "error"

    status_badge(f"Confidence: {confidence}", status)
