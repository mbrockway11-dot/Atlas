"""Atlas Validation Lab page."""

import pandas as pd
import streamlit as st

from atlas.acf.builder import build_acf_profile
from atlas.library.profile_library import list_saved_profiles
from atlas.research import (
    build_feature_correlation_audit,
    build_feature_variance_audit,
    build_profile_matrix_rows,
    compare_profile_feature_importance,
    summarize_feature_importance,
)


def render_validation_lab_page() -> None:
    """Render Atlas Validation Lab."""
    st.header("Atlas Validation Lab")
    st.caption("Audit which features actually distinguish profiles.")

    profiles = list_saved_profiles()

    if len(profiles) < 2:
        st.info("Build at least two profiles first.")
        return

    selected_profiles = st.multiselect(
        "Profiles for population audit",
        profiles,
        default=profiles[: min(5, len(profiles))],
    )

    if len(selected_profiles) < 2:
        st.warning("Select at least two profiles.")
        return

    rows = build_rows_for_profiles(selected_profiles)

    tab_variance, tab_correlation, tab_importance, tab_matrix = st.tabs(
        [
            "Feature Variance",
            "Feature Correlation",
            "Feature Importance",
            "Research Matrix",
        ]
    )

    with tab_variance:
        render_variance_tab(rows)

    with tab_correlation:
        render_correlation_tab(rows)

    with tab_importance:
        render_importance_tab(profiles)

    with tab_matrix:
        render_matrix_tab(rows)


def build_rows_for_profiles(profile_keys: list[str]) -> list[dict]:
    """Build research rows for selected saved profiles."""
    rows = []

    for profile_key in profile_keys:
        # Use the profile key as fallback name if no loader is available.
        name = profile_key.replace("_", " ").title()
        acf = build_acf_profile(name)
        rows.extend(build_profile_matrix_rows(acf))

    return rows


def render_variance_tab(rows: list[dict]) -> None:
    """Render feature variance audit."""
    st.markdown("## Feature Variance")

    audit = build_feature_variance_audit(rows)
    dataframe = pd.DataFrame(audit)

    st.dataframe(dataframe, use_container_width=True)

    st.info(
        "High-variance features are more useful for distinguishing profiles. "
        "Low-variance features may be structurally constant or over-normalized."
    )


def render_correlation_tab(rows: list[dict]) -> None:
    """Render feature correlation audit."""
    st.markdown("## Feature Correlation")

    audit = build_feature_correlation_audit(rows)
    dataframe = pd.DataFrame(audit)

    st.dataframe(dataframe, use_container_width=True)

    st.info(
        "Near-duplicate correlations suggest redundant measurements. "
        "Those features should not all be allowed to dominate similarity scoring."
    )


def render_importance_tab(profiles: list[str]) -> None:
    """Render pairwise feature importance audit."""
    st.markdown("## Feature Importance")

    col1, col2 = st.columns(2)

    with col1:
        profile_a = st.selectbox(
            "Profile A",
            profiles,
            key="validation_profile_a",
        )

    with col2:
        profile_b = st.selectbox(
            "Profile B",
            profiles,
            index=1 if len(profiles) > 1 else 0,
            key="validation_profile_b",
        )

    if profile_a == profile_b:
        st.warning("Choose two different profiles.")
        return

    name_a = profile_a.replace("_", " ").title()
    name_b = profile_b.replace("_", " ").title()

    acf_a = build_acf_profile(name_a)
    acf_b = build_acf_profile(name_b)

    rows_a = build_profile_matrix_rows(acf_a)
    rows_b = build_profile_matrix_rows(acf_b)

    importance = compare_profile_feature_importance(rows_a, rows_b)
    summary = summarize_feature_importance(importance)

    st.markdown("### Top Layer Differences")
    st.dataframe(
        pd.DataFrame(summary["top_layer_differences"]),
        use_container_width=True,
    )

    st.markdown("### Top Feature Families")
    st.dataframe(
        pd.DataFrame(summary["top_feature_families"]),
        use_container_width=True,
    )


def render_matrix_tab(rows: list[dict]) -> None:
    """Render raw research matrix."""
    st.markdown("## Research Matrix")

    dataframe = pd.DataFrame(rows)

    st.dataframe(dataframe, use_container_width=True)

    csv = dataframe.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download research_matrix.csv",
        data=csv,
        file_name="research_matrix.csv",
        mime="text/csv",
    )