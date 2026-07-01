"""Functional Role Calibration Lab page."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from atlas.services.role_calibration_service import (
    build_role_calibration_payload,
    list_role_calibration_profiles,
)


def render_role_calibration_lab_page() -> None:
    """Render Functional Role Calibration Lab."""
    st.header("Functional Role Calibration Lab")
    st.caption(
        "Audit Functional Role v2 distribution, drift, metric separation, "
        "learned role weights, and profile-level consensus."
    )

    profiles = list_role_calibration_profiles()

    if len(profiles) < 2:
        st.info("Build at least two profiles first.")
        return

    selected_profiles = st.multiselect(
        "Select profiles for calibration",
        profiles,
        default=profiles[: min(12, len(profiles))],
    )

    if len(selected_profiles) < 2:
        st.warning("Select at least two profiles.")
        return

    with st.spinner("Building role calibration payload..."):
        payload = build_role_calibration_payload(selected_profiles)

    if not payload.get("success"):
        st.error("Role calibration failed.")
        for warning in payload.get("warnings", []):
            st.warning(warning)
        with st.expander("Raw failure payload", expanded=False):
            st.json(payload)
        return

    calibration = payload["calibration"]
    diagnostics = payload["diagnostics"]

    render_service_health(payload)
    render_health(calibration, diagnostics)

    tabs = st.tabs(
        [
            "Role Distribution",
            "Metric Separation",
            "Learned Weights",
            "Profile Consensus",
            "Raw",
        ]
    )

    with tabs[0]:
        render_role_distribution(calibration)

    with tabs[1]:
        render_metric_separation(calibration)

    with tabs[2]:
        render_learned_weights(calibration)

    with tabs[3]:
        render_profile_consensus(diagnostics)

    with tabs[4]:
        render_raw(payload, calibration, diagnostics)


def render_service_health(payload: dict[str, Any]) -> None:
    """Render service-level health metrics."""
    metrics = payload.get("metrics", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Selected Profiles", metrics.get("profile_count", 0))
    c2.metric("Rows Loaded", metrics.get("row_count", 0))
    c3.metric("Valid Rows", metrics.get("valid_row_count", 0))
    c4.metric("Errors", metrics.get("error_count", 0))

    for warning in payload.get("warnings", []):
        st.warning(warning)

    errors = payload.get("errors", [])
    if errors:
        with st.expander("Row Load Errors", expanded=False):
            st.json(errors)


def render_health(calibration: dict, diagnostics: dict) -> None:
    """Render calibration health summary."""
    st.markdown("## Calibration Health")

    drift = calibration.get("drift", {})
    confidence = diagnostics.get("profile_confidence_summary", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", calibration.get("row_count", 0))
    c2.metric("Profiles", diagnostics.get("profile_count", 0))
    c3.metric("Dominant Role Drift", format_percent(drift.get("dominant_role_drift")))
    c4.metric("Mean Role Consensus", format_percent(confidence.get("mean_role_consensus")))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Min Role Consensus", format_percent(confidence.get("min_role_consensus")))
    c6.metric("Max Role Consensus", format_percent(confidence.get("max_role_consensus")))
    c7.metric("Low Consensus Profiles", confidence.get("low_consensus_count", 0))
    c8.metric("Role Count", len(calibration.get("role_distribution", [])))

    with st.expander("Drift JSON", expanded=False):
        st.json(drift)

    with st.expander("Confidence Summary JSON", expanded=False):
        st.json(confidence)


def render_role_distribution(calibration: dict) -> None:
    """Render role distribution tables."""
    st.markdown("## Role Distribution")

    dataframe = pd.DataFrame(calibration.get("role_distribution", []))

    if dataframe.empty:
        st.info("No role distribution data available.")
        return

    st.dataframe(dataframe, width="stretch")

    if "role" in dataframe.columns and "ratio" in dataframe.columns:
        st.bar_chart(dataframe.set_index("role")["ratio"], width="stretch")

    st.download_button(
        "Download role_distribution.csv",
        data=dataframe.to_csv(index=False).encode("utf-8"),
        file_name="role_distribution.csv",
        mime="text/csv",
    )


def render_metric_separation(calibration: dict) -> None:
    """Render metric separation."""
    st.markdown("## Metric Separation")

    dataframe = pd.DataFrame(calibration.get("metric_separation", []))

    if dataframe.empty:
        st.info("No metric separation data available.")
        return

    st.dataframe(dataframe, width="stretch")

    chart_columns = [
        column
        for column in [
            "between_role_variance",
            "within_role_variance",
            "separation_ratio",
        ]
        if column in dataframe.columns
    ]

    if "metric" in dataframe.columns and chart_columns:
        chart_df = dataframe.set_index("metric")[chart_columns]
        st.bar_chart(chart_df, width="stretch")

    st.download_button(
        "Download metric_separation.csv",
        data=dataframe.to_csv(index=False).encode("utf-8"),
        file_name="metric_separation.csv",
        mime="text/csv",
    )


def render_learned_weights(calibration: dict) -> None:
    """Render learned role weights."""
    st.markdown("## Learned Weights")

    learned_weights = calibration.get("learned_weights", {})

    if not learned_weights:
        st.info("No learned weights available.")
        return

    for role, records in learned_weights.items():
        st.markdown(f"### {role}")

        dataframe = pd.DataFrame(records)

        if dataframe.empty:
            st.info(f"No learned weights available for {role}.")
            continue

        st.dataframe(dataframe, width="stretch")

        chart_columns = [
            column
            for column in [
                "role_mean",
                "global_mean",
                "delta",
                "weight",
            ]
            if column in dataframe.columns
        ]

        if "metric" in dataframe.columns and chart_columns:
            st.bar_chart(dataframe.set_index("metric")[chart_columns], width="stretch")

        st.download_button(
            f"Download {role}_learned_weights.csv",
            data=dataframe.to_csv(index=False).encode("utf-8"),
            file_name=f"{slugify(role)}_learned_weights.csv",
            mime="text/csv",
        )


def render_profile_consensus(diagnostics: dict) -> None:
    """Render profile-level consensus."""
    st.markdown("## Profile Consensus")

    dataframe = pd.DataFrame(diagnostics.get("profile_consensus", []))

    if dataframe.empty:
        st.info("No profile consensus data available.")
        return

    st.dataframe(dataframe, width="stretch")

    if "name" in dataframe.columns and "role_consensus" in dataframe.columns:
        st.markdown("### Role Consensus")
        st.bar_chart(dataframe.set_index("name")["role_consensus"], width="stretch")

    st.download_button(
        "Download profile_consensus.csv",
        data=dataframe.to_csv(index=False).encode("utf-8"),
        file_name="profile_consensus.csv",
        mime="text/csv",
    )


def render_raw(payload: dict, calibration: dict, diagnostics: dict) -> None:
    """Render raw calibration/diagnostic JSON."""
    with st.expander("Raw Service Payload JSON"):
        st.json(payload)

    with st.expander("Raw Calibration JSON"):
        st.json(calibration)

    with st.expander("Raw Role Diagnostics JSON"):
        st.json(diagnostics)


def format_float(value: Any) -> str:
    """Format a float value."""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"


def format_percent(value: Any) -> str:
    """Format a ratio as percentage."""
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "n/a"


def slugify(value: str) -> str:
    """Build a safe filename slug."""
    return value.casefold().replace(" ", "_").replace("/", "_").replace("\\", "_")
