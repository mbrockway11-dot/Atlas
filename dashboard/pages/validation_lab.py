"""Validation Lab dashboard page.

This page is service-backed. Dashboard code renders controls, audits, and
exports only. Validation lab calculations are routed through
atlas.services.validation_lab_service.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.validation_lab_service import (
    build_pair_matrix_rows,
    build_validation_correlation_audit,
    build_validation_rows_for_profiles,
    build_validation_variance_audit,
    rows_to_dataframe,
)


DEFAULT_PROFILES = [
    "Albert Einstein",
    "Nikola Tesla",
    "Carl Jung",
    "Leonardo da Vinci",
    "Isaac Newton",
]


def render_validation_lab_page() -> None:
    """Render validation lab page."""
    st.header("Validation Lab")
    st.caption("Feature variance, correlation, comparison, and research matrix inspection.")

    profiles_text = st.text_area(
        "Profiles",
        value="\n".join(DEFAULT_PROFILES),
        height=150,
    )

    profiles = [
        line.strip()
        for line in profiles_text.splitlines()
        if line.strip()
    ]

    if not profiles:
        st.info("Enter at least one profile name.")
        return

    selected_profiles = st.multiselect(
        "Selected profiles",
        profiles,
        default=profiles,
    )

    if not selected_profiles:
        st.info("Select at least one profile.")
        return

    rows = build_validation_rows_for_profiles(selected_profiles)

    tab_variance, tab_correlation, tab_importance, tab_matrix = st.tabs(
        [
            "Feature Variance",
            "Feature Correlation",
            "Pair Comparison",
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


def render_variance_tab(rows: list[dict]) -> None:
    """Render variance audit."""
    st.markdown("## Feature Variance")

    audit = build_validation_variance_audit(rows)

    if isinstance(audit, dict):
        st.json(audit)
    else:
        st.write(audit)


def render_correlation_tab(rows: list[dict]) -> None:
    """Render correlation audit."""
    st.markdown("## Feature Correlation")

    audit = build_validation_correlation_audit(rows)

    if isinstance(audit, dict):
        st.json(audit)
    else:
        st.write(audit)


def render_importance_tab(profiles: list[str]) -> None:
    """Render pair comparison tab."""
    st.markdown("## Pair Comparison")

    if len(profiles) < 2:
        st.info("At least two profiles are required.")
        return

    c1, c2 = st.columns(2)
    name_a = c1.selectbox("Profile A", profiles, index=0)
    name_b = c2.selectbox("Profile B", profiles, index=1 if len(profiles) > 1 else 0)

    if name_a == name_b:
        st.warning("Choose two different profiles.")
        return

    rows_a, rows_b = build_pair_matrix_rows(name_a, name_b)

    df_a = rows_to_dataframe(rows_a)
    df_b = rows_to_dataframe(rows_b)

    st.markdown("### Profile A Matrix")
    st.dataframe(df_a, use_container_width=True)

    st.markdown("### Profile B Matrix")
    st.dataframe(df_b, use_container_width=True)

    numeric_a = df_a.select_dtypes(include="number")
    numeric_b = df_b.select_dtypes(include="number")

    if numeric_a.empty or numeric_b.empty:
        st.info("No numeric columns available for comparison.")
        return

    mean_a = numeric_a.mean(numeric_only=True)
    mean_b = numeric_b.mean(numeric_only=True)

    common = sorted(set(mean_a.index).intersection(mean_b.index))
    comparison = pd.DataFrame(
        [
            {
                "metric": metric,
                "profile_a_mean": float(mean_a[metric]),
                "profile_b_mean": float(mean_b[metric]),
                "difference": float(mean_a[metric] - mean_b[metric]),
                "absolute_difference": abs(float(mean_a[metric] - mean_b[metric])),
            }
            for metric in common
        ]
    )

    if comparison.empty:
        st.info("No common numeric metrics found.")
        return

    comparison = comparison.sort_values(
        by="absolute_difference",
        ascending=False,
    )

    st.markdown("### Largest Mean Metric Differences")
    st.dataframe(comparison.head(50), use_container_width=True)


def render_matrix_tab(rows: list[dict]) -> None:
    """Render raw research matrix."""
    st.markdown("## Research Matrix")

    df = rows_to_dataframe(rows)

    st.dataframe(df, use_container_width=True)

    st.download_button(
        "Download research_matrix.csv",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="research_matrix.csv",
        mime="text/csv",
    )