
"""Developer diagnostics section for Atlas dossiers."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.layout import divider
from dashboard.ui.metrics import metric_grid


def render_diagnostics_section(profile: dict[str, Any]) -> None:
    """Render developer-only diagnostics."""

    divider("Developer Diagnostics")

    diagnostics = profile.get("diagnostics", {})
    metrics = profile.get("metrics", {})

    if not isinstance(diagnostics, dict):
        diagnostics = {}

    if not isinstance(metrics, dict):
        metrics = {}

    metric_grid(
        {
            "Compiler": diagnostics.get("compiler", "unknown"),
            "Warnings": len(diagnostics.get("warnings", []) or []),
            "Errors": len(diagnostics.get("errors", []) or []),
            "Created At": diagnostics.get("created_at", "unknown"),
        }
    )

    render_warnings_errors(diagnostics)
    render_metrics(metrics)
    render_raw(profile)


def render_warnings_errors(diagnostics: dict[str, Any]) -> None:
    """Render warnings and errors."""

    warnings = diagnostics.get("warnings", []) or []
    errors = diagnostics.get("errors", []) or []

    if warnings:
        st.markdown("### Warnings")
        for item in warnings:
            st.warning(str(item))

    if errors:
        st.markdown("### Errors")
        for item in errors:
            st.error(str(item))


def render_metrics(metrics: dict[str, Any]) -> None:
    """Render layer metrics."""

    if not metrics:
        return

    st.markdown("### Layer Metrics")

    metric_grid(
        {
            str(key): value
            for key, value in metrics.items()
        }
    )


def render_raw(profile: dict[str, Any]) -> None:
    """Render collapsed raw payload."""

    with st.expander("Raw Dossier Payload", expanded=False):
        st.json(profile)

