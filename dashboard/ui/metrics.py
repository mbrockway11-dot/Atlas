"""Atlas UI metric helpers."""

from __future__ import annotations

from typing import Any

import streamlit as st


def metric_grid(metrics: dict[str, Any], *, columns: int = 4) -> None:
    """Render metrics in a stable grid."""
    if not metrics:
        return

    cols = st.columns(min(columns, len(metrics)))

    for index, (label, value) in enumerate(metrics.items()):
        cols[index % len(cols)].metric(str(label), value)


def confidence_meter(label: str, value: float | int | str) -> None:
    """Render a simple confidence meter."""
    try:
        numeric = float(str(value).replace("%", ""))
    except ValueError:
        st.metric(label, value)
        return

    st.metric(label, f"{numeric:.1f}%")
    st.progress(max(0, min(int(numeric), 100)))


def layer_scores(scores: dict[str, float | int | str]) -> None:
    """Render layer score meters."""
    for label, value in scores.items():
        confidence_meter(label, value)
