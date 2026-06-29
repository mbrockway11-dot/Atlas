"""Profile Test Lab page."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from atlas.diagnostics import audit_research_matrix
from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles
from atlas.research import (
    build_feature_correlation_audit,
    build_feature_variance_audit,
    build_profile_matrix_rows,
)


LEGACY_COLUMNS = [
    "kamea_score",
]


def render_profile_test_lab_page() -> None:
    """Render Profile Test Lab."""
    st.header("Profile Test Lab")
    st.caption(
        "Test whether saved profiles are producing meaningfully different graph data."
    )

    profiles = list_saved_profiles()

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

    rows = load_matrix_rows(selected_profiles)

    if not rows:
        st.error("No research rows could be loaded.")
        return

    render_summary(selected_profiles, rows)

    tab_matrix, tab_diagnostics, tab_describe, tab_variance, tab_correlation, tab_by_planet = st.tabs(
        [
            "Research Matrix",
            "Research Diagnostics",
            "Metric Describe",
            "Feature Variance",
            "Feature Correlation",
            "Planet Breakdown",
        ]
    )

    with tab_matrix:
        render_matrix(rows)

    with tab_diagnostics:
        render_diagnostics(rows)

    with tab_describe:
        render_metric_describe(rows)

    with tab_variance:
        render_variance(rows)

    with tab_correlation:
        render_correlation(rows)

    with tab_by_planet:
        render_planet_breakdown(rows)


def load_matrix_rows(profile_keys: list[str]) -> list[dict]:
    """Load ACF files and convert them into canonical research matrix rows."""
    rows = []

    for profile_key in profile_keys:
        acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"

        if not acf_path.exists():
            continue

        acf = json.loads(acf_path.read_text(encoding="utf-8"))
        profile_rows = build_profile_matrix_rows(acf)

        for row in profile_rows:
            remove_legacy_columns(row)

        rows.extend(profile_rows)

    return rows


def remove_legacy_columns(row: dict) -> dict:
    """Remove deprecated dashboard/research columns from a row."""
    for column in LEGACY_COLUMNS:
        row.pop(column, None)

    return row


def clean_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Remove deprecated columns from dashboard display/export data."""
    return dataframe.drop(
        columns=[
            column
            for column in LEGACY_COLUMNS
            if column in dataframe.columns
        ],
    )


def numeric_dataframe(rows: list[dict]) -> pd.DataFrame:
    """Return numeric-only research dataframe."""
    dataframe = clean_dataframe(pd.DataFrame(rows))

    excluded = {
        "name",
        "cipher",
        "planet",
        "kamea",
        "subtype_primary",
        "subtype_secondary",
    }

    numeric_columns = [
        column
        for column in dataframe.columns
        if column not in excluded
        and pd.api.types.is_numeric_dtype(dataframe[column])
    ]

    return dataframe[numeric_columns]


def render_summary(profile_keys: list[str], rows: list[dict]) -> None:
    """Render top summary metrics."""
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Profiles", len(profile_keys))
    c2.metric("Rows", len(rows))
    c3.metric("Expected Rows", len(profile_keys) * 21)
    c4.metric("Features", len(rows[0].keys()) if rows else 0)

    if len(rows) != len(profile_keys) * 21:
        st.warning(
            "Some selected profiles did not produce 21 rows. Rebuild those profiles."
        )

    if rows and any(
        column in row
        for row in rows
        for column in LEGACY_COLUMNS
    ):
        st.error(
            "Legacy research columns detected in dashboard rows. "
            "Atlas Studio removed them before display/export."
        )


def render_matrix(rows: list[dict]) -> None:
    """Render raw research matrix."""
    st.markdown("## Research Matrix")

    dataframe = clean_dataframe(pd.DataFrame(rows))

    st.dataframe(
        dataframe,
        width="stretch",
    )

    csv = dataframe.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download profile_test_matrix.csv",
        data=csv,
        file_name="profile_test_matrix.csv",
        mime="text/csv",
    )


def render_diagnostics(rows: list[dict]) -> None:
    """Render research diagnostics audit."""
    st.markdown("## Research Diagnostics")

    clean_rows = [
        remove_legacy_columns(dict(row))
        for row in rows
    ]

    audit = audit_research_matrix(clean_rows)

    if not audit["valid"]:
        st.error("Research diagnostics audit is invalid.")
        st.json(audit)
        return

    metrics = audit["metrics"]
    dataframe = pd.DataFrame(metrics)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Rows Audited", audit["row_count"])
    c2.metric("Numeric Metrics", audit["metric_count"])
    c3.metric(
        "A/B Metrics",
        len(
            [
                metric
                for metric in metrics
                if metric["quality_grade"] in ["A", "B"]
            ]
        ),
    )
    c4.metric(
        "D/F Metrics",
        len(
            [
                metric
                for metric in metrics
                if metric["quality_grade"] in ["D", "F"]
            ]
        ),
    )

    grade_counts = (
        dataframe["quality_grade"]
        .value_counts()
        .reset_index()
        .rename(
            columns={
                "quality_grade": "grade",
                "count": "metric_count",
            }
        )
    )

    st.markdown("### Metric Quality Grades")
    st.dataframe(
        grade_counts,
        width="stretch",
    )

    preferred_columns = [
        "metric",
        "quality_grade",
        "quality_rank",
        "mean",
        "median",
        "std",
        "variance",
        "range",
        "minimum",
        "maximum",
        "unique_value_count",
        "constant_ratio",
        "coefficient_of_variation",
        "diagnostic",
    ]

    visible_columns = [
        column
        for column in preferred_columns
        if column in dataframe.columns
    ]

    st.markdown("### Strongest Metrics")
    strongest = dataframe.sort_values(
        by=["quality_rank", "std", "unique_value_count"],
        ascending=False,
    ).head(12)

    st.dataframe(
        strongest[visible_columns],
        width="stretch",
    )

    st.markdown("### Weakest / Most Compressed Metrics")
    weakest = dataframe.sort_values(
        by=["quality_rank", "std", "unique_value_count"],
        ascending=True,
    ).head(12)

    st.dataframe(
        weakest[visible_columns],
        width="stretch",
    )

    st.markdown("### Full Metric Audit Table")
    st.dataframe(
        dataframe[visible_columns],
        width="stretch",
    )

    csv = dataframe.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download research_diagnostics.csv",
        data=csv,
        file_name="research_diagnostics.csv",
        mime="text/csv",
    )


def render_metric_describe(rows: list[dict]) -> None:
    """Render pandas descriptive statistics for numeric metrics."""
    st.markdown("## Metric Describe")

    dataframe = numeric_dataframe(rows)

    if dataframe.empty:
        st.info("No numeric metrics available.")
        return

    describe = dataframe.describe().transpose().reset_index()
    describe = describe.rename(columns={"index": "metric"})

    st.markdown("### Numeric Metric Summary")
    st.dataframe(
        describe,
        width="stretch",
    )

    st.markdown("### Selected Metric Distribution")

    metric = st.selectbox(
        "Metric",
        sorted(dataframe.columns),
    )

    selected = dataframe[metric].dropna()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Minimum", format_float(selected.min()))
    c2.metric("Maximum", format_float(selected.max()))
    c3.metric("Mean", format_float(selected.mean()))
    c4.metric("Std", format_float(selected.std()))

    st.bar_chart(
        selected.value_counts().sort_index(),
        width="stretch",
    )

    csv = describe.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download metric_describe.csv",
        data=csv,
        file_name="metric_describe.csv",
        mime="text/csv",
    )


def render_variance(rows: list[dict]) -> None:
    """Render feature variance audit."""
    st.markdown("## Feature Variance")

    clean_rows = [
        remove_legacy_columns(dict(row))
        for row in rows
    ]

    audit = build_feature_variance_audit(clean_rows)
    dataframe = clean_dataframe(pd.DataFrame(audit))

    st.dataframe(
        dataframe,
        width="stretch",
    )

    if dataframe.empty or "variance_class" not in dataframe.columns:
        st.info("No variance audit rows available.")
        return

    low_variance = dataframe[
        dataframe["variance_class"].isin(["none", "low"])
    ]

    high_variance = dataframe[
        dataframe["variance_class"].isin(["high", "very_high"])
    ]

    c1, c2 = st.columns(2)

    c1.metric("High-Variance Features", len(high_variance))
    c2.metric("Low/Dead Features", len(low_variance))

    st.info(
        "High-variance features are currently better candidates for profile "
        "separation. Low-variance features may be too constant across the corpus."
    )


def render_correlation(rows: list[dict]) -> None:
    """Render feature correlation audit."""
    st.markdown("## Feature Correlation")

    clean_rows = [
        remove_legacy_columns(dict(row))
        for row in rows
    ]

    audit = build_feature_correlation_audit(clean_rows)
    dataframe = clean_dataframe(pd.DataFrame(audit))

    st.dataframe(
        dataframe,
        width="stretch",
    )

    if dataframe.empty or "correlation_class" not in dataframe.columns:
        st.info("No correlation audit rows available.")
        return

    near_duplicates = dataframe[
        dataframe["correlation_class"] == "near_duplicate"
    ]

    st.metric("Near-Duplicate Feature Pairs", len(near_duplicates))

    if not near_duplicates.empty:
        st.warning(
            "Near-duplicate features may be redundant and should not all dominate "
            "similarity."
        )


def render_planet_breakdown(rows: list[dict]) -> None:
    """Render grouped metrics by planet."""
    st.markdown("## Planet Breakdown")

    dataframe = clean_dataframe(pd.DataFrame(rows))

    required_columns = [
        "planet",
        "node_coverage",
        "density",
        "entropy",
        "max_depth",
        "unique_edges",
        "self_loops",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        st.error(
            "Planet breakdown is missing required columns: "
            + ", ".join(missing_columns)
        )
        return

    group = dataframe.groupby("planet").agg(
        {
            "node_coverage": "mean",
            "density": "mean",
            "entropy": "mean",
            "max_depth": "mean",
            "unique_edges": "mean",
            "self_loops": "mean",
        }
    ).reset_index()

    st.dataframe(
        group,
        width="stretch",
    )


def format_float(value) -> str:
    """Format numeric values safely."""
    if value is None:
        return "n/a"

    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return str(value)