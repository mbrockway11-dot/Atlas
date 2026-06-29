"""Functional Role Calibration Lab page."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from atlas.classification.role_calibration import calibrate_functional_roles_v2
from atlas.classification.role_diagnostics import audit_functional_roles_v2
from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles
from atlas.research import build_profile_matrix_rows


def render_role_calibration_lab_page() -> None:
    """Render Functional Role Calibration Lab."""
    st.header("Functional Role Calibration Lab")
    st.caption(
        "Audit Functional Role v2 distribution, drift, metric separation, "
        "learned weights, and layer consensus."
    )

    profiles = list_saved_profiles()

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

    rows = load_matrix_rows(selected_profiles)

    if not rows:
        st.error("No research rows could be loaded.")
        return

    calibration = calibrate_functional_roles_v2(rows)
    diagnostics = audit_functional_roles_v2(rows)

    render_health(calibration, diagnostics)

    tab_distribution, tab_separation, tab_weights, tab_consensus, tab_raw = st.tabs(
        [
            "Role Distribution",
            "Metric Separation",
            "Learned Weights",
            "Profile Consensus",
            "Raw JSON",
        ]
    )

    with tab_distribution:
        render_role_distribution(calibration)

    with tab_separation:
        render_metric_separation(calibration)

    with tab_weights:
        render_learned_weights(calibration)

    with tab_consensus:
        render_profile_consensus(diagnostics)

    with tab_raw:
        render_raw(calibration, diagnostics)


def load_matrix_rows(profile_keys: list[str]) -> list[dict]:
    """Load saved ACF files and convert them to research rows."""
    rows = []

    for profile_key in profile_keys:
        acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"

        if not acf_path.exists():
            continue

        acf = json.loads(acf_path.read_text(encoding="utf-8"))
        rows.extend(build_profile_matrix_rows(acf))

    return rows


def render_health(calibration: dict, diagnostics: dict) -> None:
    """Render top-level classifier health metrics."""
    st.markdown("## Classifier Health")

    drift = calibration["drift"]
    confidence = diagnostics["profile_confidence_summary"]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Rows", calibration["row_count"])
    c2.metric("Profiles", diagnostics["profile_count"])
    c3.metric("Mean Confidence", format_float(confidence["mean"]))
    c4.metric("Hybrid Ratio", format_percent(confidence["hybrid_ratio"]))

    status = drift["status"]

    if status == "balanced":
        st.success(drift["message"])
    elif status == "moderate_drift":
        st.warning(drift["message"])
    elif status == "severe_drift":
        st.error(drift["message"])
    else:
        st.info(drift["message"])


def render_role_distribution(calibration: dict) -> None:
    """Render role distribution tables."""
    st.markdown("## Role Distribution")

    dataframe = pd.DataFrame(calibration["role_distribution"])

    st.dataframe(
        dataframe,
        width="stretch",
    )

    st.bar_chart(
        dataframe.set_index("role")["ratio"],
        width="stretch",
    )


def render_metric_separation(calibration: dict) -> None:
    """Render metric separation ranking."""
    st.markdown("## Metric Separation")

    dataframe = pd.DataFrame(calibration["metric_separation"])

    if dataframe.empty:
        st.info("No metric separation data available.")
        return

    visible_columns = [
        "metric",
        "separation_score",
        "between_role_variance",
        "within_role_variance",
        "overall_mean",
        "overall_variance",
        "count",
    ]

    st.dataframe(
        dataframe[visible_columns],
        width="stretch",
    )

    st.markdown("### Top Separating Metrics")

    top = dataframe.head(12)

    st.bar_chart(
        top.set_index("metric")["separation_score"],
        width="stretch",
    )


def render_learned_weights(calibration: dict) -> None:
    """Render learned role weights."""
    st.markdown("## Learned Weights")

    learned_weights = calibration["learned_weights"]

    for role, records in learned_weights.items():
        st.markdown(f"### {role}")

        dataframe = pd.DataFrame(records)

        if dataframe.empty:
            st.info(f"No learned weights available for {role}.")
            continue

        visible_columns = [
            "metric",
            "weight",
            "role_mean",
            "other_mean",
            "directional_advantage",
            "separation_score",
        ]

        st.dataframe(
            dataframe[visible_columns],
            width="stretch",
        )

        st.bar_chart(
            dataframe.head(10).set_index("metric")["weight"],
            width="stretch",
        )


def render_profile_consensus(diagnostics: dict) -> None:
    """Render profile-level consensus."""
    st.markdown("## Profile Consensus")

    dataframe = pd.DataFrame(diagnostics["profile_consensus"])

    if dataframe.empty:
        st.info("No profile consensus data available.")
        return

    st.dataframe(
        dataframe,
        width="stretch",
    )

    st.markdown("### Role Consensus")

    st.bar_chart(
        dataframe.set_index("name")["role_consensus"],
        width="stretch",
    )


def render_raw(calibration: dict, diagnostics: dict) -> None:
    """Render raw calibration/diagnostic JSON."""
    with st.expander("Raw Calibration JSON"):
        st.json(calibration)

    with st.expander("Raw Role Diagnostics JSON"):
        st.json(diagnostics)


def format_float(value) -> str:
    """Format float safely."""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"


def format_percent(value) -> str:
    """Format percent safely."""
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "n/a"