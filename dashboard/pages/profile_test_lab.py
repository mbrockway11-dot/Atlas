"""Profile Test Lab dashboard page."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from atlas.services.profile_test_service import (
    build_profile_test_payload,
    list_profile_test_profiles,
)


def render_profile_test_lab_page() -> None:
    """Render service-backed Profile Test Lab."""
    st.header("Profile Test Lab")
    st.caption("Profile matrix diagnostics through the service layer.")

    profiles = list_profile_test_profiles()

    if len(profiles) < 2:
        st.info("Build at least two profiles first.")
        return

    selected_profiles = st.multiselect(
        "Select profiles to test",
        profiles,
        default=profiles[: min(8, len(profiles))],
    )

    if len(selected_profiles) < 2:
        st.warning("Select at least two profiles.")
        return

    with st.spinner("Building profile test payload..."):
        payload = call_profile_test_service(selected_profiles)

    if not payload:
        st.error("Profile Test Lab service returned no payload.")
        return

    if payload.get("success") is False:
        st.error("Profile Test Lab service failed.")
        for error in payload.get("errors", []):
            st.error(error)
        st.json(payload)
        return

    render_summary(payload, selected_profiles)

    tabs = st.tabs(
        [
            "Research Matrix",
            "Diagnostics",
            "Describe",
            "Variance",
            "Correlation",
            "Planet Breakdown",
            "Raw Payload",
        ]
    )

    with tabs[0]:
        render_dataframe_section(
            "Research Matrix",
            extract_dataframe(payload, ["rows", "matrix", "research_rows"]),
            "profile_test_matrix.csv",
        )

    with tabs[1]:
        render_dataframe_section(
            "Diagnostics",
            extract_dataframe(payload, ["diagnostics", "audit_metrics", "metrics"]),
            "profile_test_diagnostics.csv",
        )

    with tabs[2]:
        rows = extract_dataframe(payload, ["rows", "matrix", "research_rows"])
        render_describe(rows)

    with tabs[3]:
        render_dataframe_section(
            "Feature Variance",
            extract_dataframe(payload, ["variance", "variance_audit"]),
            "profile_test_variance.csv",
        )

    with tabs[4]:
        render_dataframe_section(
            "Feature Correlation",
            extract_dataframe(payload, ["correlation", "correlation_audit"]),
            "profile_test_correlation.csv",
        )

    with tabs[5]:
        render_dataframe_section(
            "Planet Breakdown",
            extract_dataframe(payload, ["planet_breakdown", "by_planet"]),
            "profile_test_planet_breakdown.csv",
        )

    with tabs[6]:
        st.json(make_json_safe(payload))


def call_profile_test_service(profile_keys: list[str]) -> dict[str, Any]:
    """Call service while tolerating positional or keyword signatures."""
    try:
        return build_profile_test_payload(profile_keys)
    except TypeError:
        return build_profile_test_payload(profile_keys=profile_keys)


def render_summary(payload: dict[str, Any], selected_profiles: list[str]) -> None:
    """Render summary metrics."""
    summary = payload.get("summary", {})
    metrics = payload.get("metrics", {})

    rows_df = extract_dataframe(payload, ["rows", "matrix", "research_rows"])

    profile_count = (
        summary.get("profile_count")
        or metrics.get("profile_count")
        or len(selected_profiles)
    )
    row_count = (
        summary.get("row_count")
        or metrics.get("row_count")
        or len(rows_df)
    )
    expected_rows = (
        summary.get("expected_rows")
        or metrics.get("expected_rows")
        or len(selected_profiles) * 21
    )
    feature_count = (
        summary.get("feature_count")
        or metrics.get("feature_count")
        or len(rows_df.columns)
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Profiles", profile_count)
    c2.metric("Rows", row_count)
    c3.metric("Expected Rows", expected_rows)
    c4.metric("Features", feature_count)

    warnings = payload.get("warnings", [])
    errors = payload.get("errors", [])

    for warning in warnings:
        st.warning(warning)

    for error in errors:
        st.error(error)

    if row_count != expected_rows:
        st.warning("Row count does not match expected 21 rows per profile.")


def render_dataframe_section(
    title: str,
    dataframe: pd.DataFrame,
    filename: str,
) -> None:
    """Render a dataframe section with download."""
    st.markdown(f"## {title}")

    if dataframe.empty:
        st.info(f"No {title.lower()} data available.")
        return

    st.dataframe(dataframe, width="stretch")

    st.download_button(
        f"Download {filename}",
        data=dataframe.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


def render_describe(dataframe: pd.DataFrame) -> None:
    """Render numeric describe table."""
    st.markdown("## Metric Describe")

    if dataframe.empty:
        st.info("No matrix rows available.")
        return

    numeric = dataframe.select_dtypes(include="number")

    if numeric.empty:
        st.info("No numeric metrics available.")
        return

    describe = numeric.describe().transpose().reset_index()
    describe = describe.rename(columns={"index": "metric"})

    st.dataframe(describe, width="stretch")

    metric = st.selectbox("Metric", sorted(numeric.columns))

    series = numeric[metric].dropna()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Minimum", format_float(series.min()))
    c2.metric("Maximum", format_float(series.max()))
    c3.metric("Mean", format_float(series.mean()))
    c4.metric("Std", format_float(series.std()))

    st.bar_chart(series.value_counts().sort_index(), width="stretch")

    st.download_button(
        "Download metric_describe.csv",
        data=describe.to_csv(index=False).encode("utf-8"),
        file_name="metric_describe.csv",
        mime="text/csv",
    )


def extract_dataframe(
    payload: dict[str, Any],
    keys: list[str],
) -> pd.DataFrame:
    """Extract dataframe from likely service payload locations."""
    for key in keys:
        value = payload.get(key)

        if value is None and isinstance(payload.get("data"), dict):
            value = payload["data"].get(key)

        dataframe = coerce_dataframe(value)

        if not dataframe.empty:
            return dataframe

    return pd.DataFrame()


def coerce_dataframe(value: Any) -> pd.DataFrame:
    """Convert common payload values into a dataframe."""
    if value is None:
        return pd.DataFrame()

    if isinstance(value, pd.DataFrame):
        return value

    if isinstance(value, list):
        return pd.DataFrame(value)

    if isinstance(value, dict):
        if "rows" in value and isinstance(value["rows"], list):
            return pd.DataFrame(value["rows"])

        if "metrics" in value and isinstance(value["metrics"], list):
            return pd.DataFrame(value["metrics"])

        if "data" in value and isinstance(value["data"], list):
            return pd.DataFrame(value["data"])

        return pd.DataFrame([value])

    return pd.DataFrame()


def make_json_safe(value: Any) -> Any:
    """Convert pandas and non-JSON values into Streamlit-safe objects."""
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")

    if isinstance(value, dict):
        return {key: make_json_safe(item) for key, item in value.items()}

    if isinstance(value, list):
        return [make_json_safe(item) for item in value]

    return value


def format_float(value: Any) -> str:
    """Format numeric values safely."""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"