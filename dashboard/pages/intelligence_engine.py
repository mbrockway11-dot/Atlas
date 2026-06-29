"""Intelligence Engine dashboard page."""

from __future__ import annotations

from pathlib import Path
import json

import streamlit as st

from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles
from atlas.intelligence.engine import (
    IntelligenceEngineConfig,
    build_intelligence_payload,
)


def render_intelligence_engine_page() -> None:
    """Render Atlas Intelligence Engine page."""
    st.header("Intelligence Engine")
    st.caption(
        "Unified orchestration layer for identity, research session, population position, "
        "statistical position, topology role, evidence, and confidence."
    )

    profile_keys = list_saved_profiles()

    if not profile_keys:
        st.error("No saved profiles found in the profile library.")
        return

    selected_profile = st.selectbox(
        "Profile",
        profile_keys,
        index=0,
    )

    with st.sidebar.expander("Intelligence Engine Settings", expanded=False):
        transit_date = st.text_input("Transit date", value="2026-06-29")
        neighbor_limit = st.slider("Neighbor limit", 1, 25, 10)
        cluster_count = st.slider("Cluster count", 2, 20, 5)
        principal_components = st.slider("Principal components", 2, 5, 3)
        topology_threshold = st.slider("Topology threshold", 0.0, 1.0, 0.75, 0.01)
        topology_top_k = st.slider("Topology top-k", 0, 20, 5)
        similarity_metric = st.radio(
            "Similarity metric",
            ["cosine", "euclidean"],
            horizontal=True,
        )

    config = IntelligenceEngineConfig(
        transit_date=transit_date,
        neighbor_limit=neighbor_limit,
        cluster_count=cluster_count,
        principal_components=principal_components,
        topology_threshold=topology_threshold,
        topology_top_k=topology_top_k,
        similarity_metric=similarity_metric,
    )

    profile_dir = LIBRARY_DIR / selected_profile

    if not profile_dir.exists():
        st.error(f"Profile directory not found: {profile_dir}")
        return

    try:
        payload = build_intelligence_payload(profile_dir, config=config)
    except Exception as exc:
        st.error("Intelligence Engine failed.")
        st.exception(exc)
        return

    render_overview(payload)

    tab_research, tab_population, tab_statistics, tab_topology, tab_evidence, tab_raw = st.tabs(
        [
            "Research Session",
            "Population",
            "Statistics",
            "Topology",
            "Evidence",
            "Raw Payload",
        ]
    )

    with tab_research:
        render_research_session(payload)

    with tab_population:
        render_population(payload)

    with tab_statistics:
        render_statistics(payload)

    with tab_topology:
        render_topology(payload)

    with tab_evidence:
        render_evidence(payload)

    with tab_raw:
        render_raw(payload)


def render_overview(payload: dict) -> None:
    """Render top-level intelligence summary."""
    profile = payload.get("profile", {})
    confidence = payload.get("confidence", {})

    st.subheader(profile.get("name", "Unknown profile"))

    c1, c2, c3 = st.columns(3)
    c1.metric("Confidence", confidence.get("label", "unavailable"))
    c2.metric("Confidence score", f"{confidence.get('score', 0.0):.2f}")
    c3.metric("Evidence count", confidence.get("evidence_count", 0))

    warnings = payload.get("warnings", [])
    for warning in warnings:
        st.warning(warning)


def render_research_session(payload: dict) -> None:
    """Render research session payload."""
    st.markdown("## Research Session")
    session = payload.get("research_session")

    if session is None:
        st.info("No research session available.")
        return

    st.json(session)


def render_population(payload: dict) -> None:
    """Render population position."""
    st.markdown("## Population Position")
    population = payload.get("population_position")

    if not population:
        st.info("No population position available.")
        return

    c1, c2 = st.columns(2)
    c1.metric("Outlier rank", population.get("outlier_rank"))
    centroid_distance = population.get("centroid_distance")
    c2.metric(
        "Centroid distance",
        "n/a" if centroid_distance is None else f"{centroid_distance:.3f}",
    )

    st.markdown("### Nearest Neighbors")
    neighbors = population.get("nearest_neighbors", [])
    if neighbors:
        st.dataframe(neighbors, use_container_width=True)
    else:
        st.info("No nearest neighbors available.")


def render_statistics(payload: dict) -> None:
    """Render statistical position."""
    st.markdown("## Statistical Position")
    stats = payload.get("statistical_position")

    if not stats:
        st.info("No statistical position available.")
        return

    st.markdown("### Cluster")
    st.json(stats.get("cluster"))

    st.markdown("### Silhouette")
    st.json(stats.get("silhouette"))

    st.markdown("### Principal Components")
    st.json(stats.get("principal_components"))

    st.markdown("### Explained Variance Ratio")
    st.write(stats.get("explained_variance_ratio", []))


def render_topology(payload: dict) -> None:
    """Render topology position."""
    st.markdown("## Topology Position")
    topology = payload.get("topology_position")

    if not topology:
        st.info("No topology position available.")
        return

    if not topology.get("available", False):
        st.warning(topology.get("reason", "Topology unavailable."))
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Degree", topology.get("degree", 0))
    c2.metric("Weighted degree", f"{topology.get('weighted_degree', 0.0):.3f}")
    c3.metric("Component", topology.get("component"))
    c4.metric("Community", topology.get("community"))

    st.markdown("### Centrality")
    st.json(
        {
            "degree_centrality": topology.get("degree_centrality"),
            "weighted_degree_centrality": topology.get("weighted_degree_centrality"),
            "closeness_centrality": topology.get("closeness_centrality"),
        }
    )


def render_evidence(payload: dict) -> None:
    """Render evidence and confidence."""
    st.markdown("## Evidence")
    evidence = payload.get("evidence", [])

    if evidence:
        st.dataframe(evidence, use_container_width=True)
    else:
        st.info("No evidence records available.")

    st.markdown("## Confidence")
    st.json(payload.get("confidence", {}))


def render_raw(payload: dict) -> None:
    """Render raw payload export."""
    st.markdown("## Raw Intelligence Payload")
    st.json(payload)

    st.download_button(
        "Download intelligence_payload.json",
        data=json.dumps(payload, indent=2, sort_keys=True),
        file_name="intelligence_payload.json",
        mime="application/json",
    )