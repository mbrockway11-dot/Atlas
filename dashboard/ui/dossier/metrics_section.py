
"""Layer Metrics section for Atlas dossiers."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.layout import divider
from dashboard.ui.metrics import metric_grid


def render_metrics_section(profile: dict[str, Any]) -> None:
    """Render compiler and layer metrics."""

    divider("Layer Metrics")

    metrics = profile.get("metrics", {})

    if not isinstance(metrics, dict) or not metrics:
        st.info("No layer metrics are available.")
        return

    metric_grid({str(key): value for key, value in metrics.items()})

    with st.expander("Raw Metrics", expanded=False):
        st.json(metrics)

