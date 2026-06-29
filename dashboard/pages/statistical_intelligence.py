"""Statistical Intelligence dashboard page."""

from __future__ import annotations

from pathlib import Path
import json

import pandas as pd
import streamlit as st

from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles
from atlas.research.matrix import build_profile_matrix_rows
from atlas.research.statistical import (
    build_statistical_intelligence_report,
    cluster_summary,
    cohort_separation,
    kmeans_clusters,
    principal_components,
    silhouette_scores,
    statistical_report_to_json,
)
from atlas.research.validation import build_profile_feature_matrix, load_cohort_index

DEFAULT_COHORT_INDEX = Path("research/profile_intake/cohort_index.csv")


def render_statistical_intelligence_page() -> None:
    """Render Atlas Statistical Intelligence."""
    st.header("Statistical Intelligence")
    st.caption(
        "Phase 5: measure population structure using existing profile metrics. "
        "No new symbolic engine is added here."
    )

    matrix = load_profile_library_matrix()
    if matrix.empty:
        st.error("No profile matrix rows could be loaded from the profile library.")
        return

    profile_features = build_profile_feature_matrix(matrix)
    if profile_features.empty or len(profile_features) < 2:
        st.error("At least two profiles are required for Statistical Intelligence.")
        return

    cohort_path = st.text_input("Optional cohort index CSV", value=str(DEFAULT_COHORT_INDEX))
    cohort_index = load_cohort_index(cohort_path)

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

    report = build_statistical_intelligence_report(
        profile_features,
        cohort_index=cohort_index,
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
        render_cohorts(profile_features, cohort_index)

    with tab_exports:
        render_exports(report)


def load_profile_library_matrix() -> pd.DataFrame:
    """Load every saved profile into the row-level research matrix."""
    rows: list[dict] = []

    for profile_key in list_saved_profiles():
        acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"
        if not acf_path.exists():
            continue

        try:
            acf = json.loads(acf_path.read_text(encoding="utf-8"))
            rows.extend(build_profile_matrix_rows(acf))
        except Exception as exc:
            st.warning(f"Skipped {profile_key}: {exc}")

    return pd.DataFrame(rows)


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
    pca = principal_components(profile_features, n_components=n_components)

    if not pca["available"]:
        st.warning(pca["reason"])
        return

    explained = pd.DataFrame(
        [
            {"component": f"PC{index + 1}", "explained_variance_ratio": value}
            for index, value in enumerate(pca["explained_variance_ratio"])
        ]
    )
    st.dataframe(explained, use_container_width=True)

    coordinates = pd.DataFrame(pca["coordinates"])
    st.markdown("### Profile Coordinates")
    st.dataframe(coordinates, use_container_width=True)

    if {"pc1", "pc2"}.issubset(coordinates.columns):
        st.scatter_chart(coordinates, x="pc1", y="pc2")

    st.markdown("### Top Feature Loadings")
    for component, rows in pca["top_loadings"].items():
        with st.expander(component.upper(), expanded=component == "pc1"):
            st.dataframe(pd.DataFrame(rows), use_container_width=True)


def render_clusters(profile_features: pd.DataFrame, k: int) -> None:
    """Render deterministic k-means clusters."""
    st.markdown("## Deterministic Cluster Analysis")
    assignments = kmeans_clusters(profile_features, k=k)
    summary = cluster_summary(assignments)

    st.markdown("### Cluster Summary")
    st.dataframe(summary, use_container_width=True)

    st.markdown("### Assignments")
    st.dataframe(assignments, use_container_width=True)


def render_silhouette(profile_features: pd.DataFrame, k: int) -> None:
    """Render silhouette coherence scores."""
    st.markdown("## Silhouette Coherence")
    assignments = kmeans_clusters(profile_features, k=k)
    scores = silhouette_scores(profile_features, assignments)

    if scores.empty:
        st.info("Silhouette scores are unavailable for the current data.")
        return

    st.metric("Mean silhouette", f"{scores['silhouette'].mean():.3f}")
    st.caption("Higher is cleaner separation. Near zero means overlap. Negative means likely misassignment.")
    st.dataframe(scores, use_container_width=True)


def render_cohorts(profile_features: pd.DataFrame, cohort_index: pd.DataFrame) -> None:
    """Render cohort separation metrics."""
    st.markdown("## Cohort Separation")
    separation = cohort_separation(profile_features, cohort_index)

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
    st.dataframe(pd.DataFrame(separation["cohorts"]), use_container_width=True)


def render_exports(report: dict) -> None:
    """Render report export controls."""
    st.markdown("## Exports")
    st.download_button(
        "Download statistical_intelligence_report.json",
        data=statistical_report_to_json(report),
        file_name="statistical_intelligence_report.json",
        mime="application/json",
    )