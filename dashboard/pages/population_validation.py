"""Population Validation Lab dashboard page.

This page is service-backed. Dashboard code should render controls, tables,
charts, and downloads only. Population validation calculations are routed
through atlas.services.validation_service.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.validation_service import (
    DEFAULT_COHORT_INDEX,
    get_cohort_index,
    get_correlated_feature_pairs,
    get_data_quality,
    get_feature_variance,
    get_nearest_neighbors,
    get_numeric_columns,
    get_outlier_scores,
    get_population_matrix,
    get_population_validation_report,
    get_profile_feature_matrix,
    validation_report_json,
)


def render_population_validation_page() -> None:
    """Render Population Validation Lab."""
    st.header("Population Validation Lab")
    st.caption(
        "Validate whether the generated population matrix has coherent, "
        "discriminating structure before adding more engines."
    )

    matrix = get_population_matrix()

    if matrix.empty:
        st.error("No profile matrix rows could be loaded from the profile library.")
        return

    cohort_path = st.text_input(
        "Optional cohort index CSV",
        value=str(DEFAULT_COHORT_INDEX),
    )

    correlation_threshold = st.slider(
        "High-correlation threshold",
        min_value=0.80,
        max_value=1.00,
        value=0.95,
        step=0.01,
    )

    cohort_index = get_cohort_index(cohort_path)
    profile_features = get_profile_feature_matrix(matrix)
    report = get_population_validation_report(
        cohort_path=cohort_path,
        correlation_threshold=correlation_threshold,
    )

    render_summary(matrix)

    tab_quality, tab_variance, tab_neighbors, tab_outliers, tab_correlation, tab_cohorts, tab_exports = st.tabs(
        [
            "Data Quality",
            "Feature Variance",
            "Nearest Neighbors",
            "Outliers",
            "Feature Redundancy",
            "Cohorts",
            "Exports",
        ]
    )

    with tab_quality:
        render_quality(matrix)

    with tab_variance:
        render_variance(matrix, report)

    with tab_neighbors:
        render_neighbors(profile_features)

    with tab_outliers:
        render_outliers(profile_features)

    with tab_correlation:
        render_correlation(profile_features, correlation_threshold)

    with tab_cohorts:
        render_cohorts(report, cohort_index)

    with tab_exports:
        render_exports(report, profile_features)


def render_summary(matrix: pd.DataFrame) -> None:
    """Render corpus summary cards."""
    numeric = get_numeric_columns(matrix)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Rows", len(matrix))
    c2.metric("Profiles", matrix["name"].nunique() if "name" in matrix else 0)
    c3.metric("Ciphers", matrix["cipher"].nunique() if "cipher" in matrix else 0)
    c4.metric("Planets/Kameas", matrix["planet"].nunique() if "planet" in matrix else 0)
    c5.metric("Numeric Metrics", len(numeric))


def render_quality(matrix: pd.DataFrame) -> None:
    """Render data quality checks."""
    st.markdown("## Data Quality Checks")
    quality = get_data_quality(matrix)

    c1, c2, c3 = st.columns(3)
    c1.metric("Duplicate profile/cipher/planet rows", quality["duplicate_profile_cipher_planet_rows"])
    c2.metric("Expected rows/profile", quality["expected_rows_per_profile"])
    c3.metric("Profiles missing realizations", quality["profile_count_with_missing_realizations"])

    st.markdown("### Missing Values")
    if quality["missing_values"]:
        st.dataframe(
            pd.DataFrame(
                [
                    {"column": column, "missing_count": count}
                    for column, count in quality["missing_values"].items()
                ]
            ),
            use_container_width=True,
        )
    else:
        st.success("No missing values detected.")

    st.markdown("### Rows per Profile")
    rows_per_profile = pd.DataFrame(
        [
            {"name": name, "row_count": count}
            for name, count in quality["rows_per_profile"].items()
        ]
    )
    st.dataframe(rows_per_profile, use_container_width=True)

    if quality["profiles_missing_realizations"]:
        st.warning("Some profiles do not have exactly 21 rows.")
        st.json(quality["profiles_missing_realizations"])
    else:
        st.success("All profiles have the expected 21 cipher/planet realizations.")


def render_variance(matrix: pd.DataFrame, report: dict) -> None:
    """Render feature variance audit."""
    st.markdown("## Feature Variance")

    variance = report.get("feature_variance")
    if variance is None:
        variance = get_feature_variance(matrix)

    c1, c2 = st.columns(2)
    c1.metric("Zero-variance columns", len(variance["zero_variance_columns"]))
    c2.metric("Low-variance columns", len(variance["low_variance_columns"]))

    st.markdown("### Highest Variance Columns")
    st.dataframe(pd.DataFrame(variance["highest_variance_columns"]), use_container_width=True)

    with st.expander("Zero-variance columns", expanded=False):
        st.write(variance["zero_variance_columns"])

    with st.expander("Low-variance columns", expanded=False):
        st.write(variance["low_variance_columns"])


def render_neighbors(profile_features: pd.DataFrame) -> None:
    """Render nearest-neighbor validation."""
    st.markdown("## Nearest-Neighbor Validation")

    names = sorted(profile_features["name"].tolist()) if "name" in profile_features else []
    if len(names) < 2:
        st.info("At least two profiles are required for nearest-neighbor validation.")
        return

    selected = st.selectbox("Selected profile", names)
    metric = st.radio("Distance metric", ["cosine", "euclidean"], horizontal=True)
    limit = st.slider("Neighbor limit", 1, min(50, len(names) - 1), min(10, len(names) - 1))

    neighbors = get_nearest_neighbors(
        profile_features,
        selected,
        limit=limit,
        metric=metric,
    )
    st.dataframe(pd.DataFrame(neighbors), use_container_width=True)


def render_outliers(profile_features: pd.DataFrame) -> None:
    """Render outlier rankings."""
    st.markdown("## Outlier Detection")
    st.caption("Profiles are ranked by distance from the normalized population centroid.")

    outliers = get_outlier_scores(profile_features)
    st.dataframe(outliers.head(100), use_container_width=True)


def render_correlation(profile_features: pd.DataFrame, threshold: float) -> None:
    """Render redundant feature pairs."""
    st.markdown("## Feature Correlation / Redundancy")
    pairs = get_correlated_feature_pairs(profile_features, threshold=threshold)

    st.metric("Highly correlated pairs", len(pairs))

    if pairs:
        st.dataframe(pd.DataFrame(pairs), use_container_width=True)
    else:
        st.success("No feature pairs exceeded the selected threshold.")


def render_cohorts(report: dict, cohort_index: pd.DataFrame) -> None:
    """Render optional cohort support."""
    st.markdown("## Cohort Support")
    support = report["cohort_support"]

    if cohort_index.empty or not support["available"]:
        st.info(
            "No cohort index found yet. Add research/profile_intake/cohort_index.csv "
            "with columns: name,cohort."
        )
        return

    st.markdown("### Cohort Counts")
    st.dataframe(
        pd.DataFrame(
            [
                {"cohort": cohort, "profile_count": count}
                for cohort, count in support["cohort_counts"].items()
            ]
        ),
        use_container_width=True,
    )

    if support["profiles_without_cohort"]:
        with st.expander("Profiles without cohort", expanded=False):
            st.write(support["profiles_without_cohort"])


def render_exports(report: dict, profile_features: pd.DataFrame) -> None:
    """Render export downloads."""
    st.markdown("## Exports")

    st.download_button(
        "Download population_validation_report.json",
        data=validation_report_json(report),
        file_name="population_validation_report.json",
        mime="application/json",
    )

    st.download_button(
        "Download profile_level_feature_matrix.csv",
        data=profile_features.to_csv(index=False).encode("utf-8"),
        file_name="profile_level_feature_matrix.csv",
        mime="text/csv",
    )
