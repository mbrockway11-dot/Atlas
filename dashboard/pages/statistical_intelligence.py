"""Statistical Intelligence dashboard page.

This page is service-backed. Dashboard code renders controls, tables, charts,
and downloads only. Statistical calculations are routed through
atlas.services.statistical_service.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.statistical_service import (
    DEFAULT_COHORT_INDEX,
    get_cluster_summary,
    get_cohort_separation,
    get_kmeans_clusters,
    get_principal_components,
    get_silhouette_scores,
    get_statistical_intelligence_report,
    get_statistical_population_matrix,
    get_statistical_profile_features,
    statistical_json,
)


def render_statistical_intelligence_page() -> None:
    """Render Atlas Statistical Intelligence."""
    st.header("Statistical Intelligence")
    st.caption(
        "Phase 5: measure population structure using existing profile metrics. "
        "No new symbolic engine is added here."
    )

    matrix = get_statistical_population_matrix()
    if matrix.empty:
        st.error("No profile matrix rows could be loaded from the profile library.")
        return

    profile_features = get_statistical_profile_features(matrix)
    if profile_features.empty or len(profile_features) < 2:
        st.error("At least two profiles are required for Statistical Intelligence.")
        return

    cohort_path = st.text_input("Optional cohort index CSV", value=str(DEFAULT_COHORT_INDEX))

    c1, c2, c3 = st.columns(3)
    k = c1.slider(
        "Cluster count",
        min_value=2,
        max_value=min(20, len(profile_features)),
        value=min(5, len(profile_features)),
    )
    n_components = c2.slider(
        "Principal components",
        min_value=2,
        max_value=min(5, len(profile_features) - 1),
        value=min(3, len(profile_features) - 1),
    )
    c3.metric("Profiles", len(profile_features))

    report = get_statistical_intelligence_report(
        profile_features,
        cohort_path=cohort_path,
        k=k,
        n_components=n_components,
    )

    render_overview(report)

    tab_pca, tab_clusters, tab_silhouette, tab_cohorts, tab_exports = st.tabs(
        [
            "Principal Components",
            "Clusters",
            "Silhouette",
            "Cohorts",
            "Exports",
        ]
    )

    with tab_pca:
        render_principal_components(profile_features, n_components)

    with tab_clusters:
        render_clusters(profile_features, k)

    with tab_silhouette:
        render_silhouette(profile_features, k)

    with tab_cohorts:
        render_cohorts(profile_features, cohort_path)

    with tab_exports:
        render_exports(report)


def render_overview(report: dict) -> None:
    """Render high-level statistical status."""
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Profiles", report["profile_count"])
    c2.metric("Profile-level features", report["feature_count"])
    c3.metric("Clusters", len(report["cluster_summary"]))

    mean_silhouette = report.get("mean_silhouette")
    c4.metric(
        "Mean silhouette",
        "n/a" if mean_silhouette is None else f"{mean_silhouette:.3f}",
    )

    pca = report["principal_components"]
    if pca["available"]:
        explained = sum(pca["explained_variance_ratio"])
        st.info(
            f"Selected principal components explain {explained:.2%} "
            "of normalized profile-level variance."
        )
    else:
        st.warning(pca["reason"])


def render_principal_components(profile_features: pd.DataFrame, n_components: int) -> None:
    """Render PCA-style dimensional reduction."""
    st.markdown("## Principal Components")
    pca = get_principal_components(profile_features, n_components=n_components)

    if not pca["available"]:
        st.warning(pca["reason"])
        return

    explained = pd.DataFrame(
        [
            {"component": f"PC{index + 1}", "explained_variance_ratio": value}
            for index, value in enumerate(pca["explained_variance_ratio"])
        ]
    )
    st.dataframe(explained, width="stretch")

    coordinates = pd.DataFrame(pca["coordinates"])
    st.markdown("### Profile Coordinates")
    st.dataframe(coordinates, width="stretch")

    if {"pc1", "pc2"}.issubset(coordinates.columns):
        st.scatter_chart(coordinates, x="pc1", y="pc2")

    st.markdown("### Top Feature Loadings")
    for component, rows in pca["top_loadings"].items():
        with st.expander(component.upper(), expanded=component == "pc1"):
            st.dataframe(pd.DataFrame(rows), width="stretch")


def render_clusters(profile_features: pd.DataFrame, k: int) -> None:
    """Render deterministic k-means clusters."""
    st.markdown("## Deterministic Cluster Analysis")
    assignments = get_kmeans_clusters(profile_features, k=k)
    summary = get_cluster_summary(assignments)

    st.markdown("### Cluster Summary")
    st.dataframe(summary, width="stretch")

    st.markdown("### Assignments")
    st.dataframe(assignments, width="stretch")


def render_silhouette(profile_features: pd.DataFrame, k: int) -> None:
    """Render silhouette coherence scores."""
    st.markdown("## Silhouette Coherence")
    assignments = get_kmeans_clusters(profile_features, k=k)
    scores = get_silhouette_scores(profile_features, assignments)

    if scores.empty:
        st.info("Silhouette scores are unavailable for the current data.")
        return

    st.metric("Mean silhouette", f"{scores['silhouette'].mean():.3f}")
    st.caption("Higher is cleaner separation. Near zero means overlap. Negative means likely misassignment.")
    st.dataframe(scores, width="stretch")


def render_cohorts(profile_features: pd.DataFrame, cohort_path: str) -> None:
    """Render cohort separation metrics."""
    st.markdown("## Cohort Separation")
    separation = get_cohort_separation(profile_features, cohort_path)

    if not separation["available"]:
        st.info(separation["reason"])
        st.caption("Add research/profile_intake/cohort_index.csv with columns: name,cohort.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Internal distance",
        f"{separation['overall_internal_distance']:.3f}"
        if separation["overall_internal_distance"] is not None
        else "n/a",
    )
    c2.metric(
        "External distance",
        f"{separation['overall_external_distance']:.3f}"
        if separation["overall_external_distance"] is not None
        else "n/a",
    )
    c3.metric(
        "Internal / external",
        f"{separation['separation_ratio']:.3f}"
        if separation["separation_ratio"] is not None
        else "n/a",
    )

    st.caption("A ratio below 1.0 means cohorts are internally tighter than they are externally distant.")
    st.dataframe(pd.DataFrame(separation["cohorts"]), width="stretch")


def render_exports(report: dict) -> None:
    """Render report export controls."""
    st.markdown("## Exports")
    st.download_button(
        "Download statistical_intelligence_report.json",
        data=statistical_json(report),
        file_name="statistical_intelligence_report.json",
        mime="application/json",
    )
