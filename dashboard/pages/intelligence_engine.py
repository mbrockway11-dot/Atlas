"""Intelligence Engine dashboard page."""

from __future__ import annotations

import json

import streamlit as st

from atlas.intelligence.models import IntelligenceEngineConfig
from atlas.services.intelligence_service import get_intelligence_payload
from atlas.services.profile_service import list_profile_keys


def render_intelligence_engine_page() -> None:
    """Render Atlas Intelligence Engine page."""
    st.header("Intelligence Engine")
    st.caption("Unified service-backed orchestration layer for Atlas intelligence payloads.")

    profile_keys = list_profile_keys()

    if not profile_keys:
        st.error("No saved profiles found.")
        return

    selected_profile = st.selectbox("Profile", profile_keys)

    with st.sidebar.expander("Intelligence Engine Settings", expanded=False):
        transit_date = st.text_input("Transit date", value="2026-06-29")
        neighbor_limit = st.slider("Neighbor limit", 1, 25, 10)
        cluster_count = st.slider("Cluster count", 2, 20, 5)
        principal_components = st.slider("Principal components", 2, 5, 3)
        topology_threshold = st.slider("Topology threshold", 0.0, 1.0, 0.75, 0.01)
        topology_top_k = st.slider("Topology top-k", 0, 20, 5)
        similarity_metric = st.radio("Similarity metric", ["cosine", "euclidean"], horizontal=True)
        use_cache = st.checkbox("Use cache", value=True)
        refresh = st.button("Refresh payload")

    config = IntelligenceEngineConfig(
        transit_date=transit_date,
        neighbor_limit=neighbor_limit,
        cluster_count=cluster_count,
        principal_components=principal_components,
        topology_threshold=topology_threshold,
        topology_top_k=topology_top_k,
        similarity_metric=similarity_metric,
    )

    try:
        payload = get_intelligence_payload(
            selected_profile,
            config=config,
            use_cache=use_cache,
            refresh=refresh,
        )
    except Exception as exc:
        st.error("Intelligence service failed.")
        st.exception(exc)
        return

    render_overview(payload)

    tab_summary, tab_research, tab_population, tab_statistics, tab_topology, tab_evidence, tab_provenance, tab_raw = st.tabs(
        [
            "Summary",
            "Research Session",
            "Population",
            "Statistics",
            "Topology",
            "Evidence",
            "Provenance",
            "Raw Payload",
        ]
    )

    with tab_summary:
        render_summary(payload)

    with tab_research:
        st.json(payload.get("research_session"))

    with tab_population:
        render_population(payload)

    with tab_statistics:
        render_statistics(payload)

    with tab_topology:
        render_topology(payload)

    with tab_evidence:
        render_evidence(payload)

    with tab_provenance:
        st.dataframe(payload.get("provenance", []), use_container_width=True)

    with tab_raw:
        render_raw(payload)


def render_overview(payload: dict) -> None:
    """Render top-level overview."""
    profile = payload.get("profile", {})
    confidence = payload.get("confidence", {})

    st.subheader(profile.get("name", "Unknown profile"))

    c1, c2, c3 = st.columns(3)
    c1.metric("Confidence", confidence.get("label", "unavailable"))
    c2.metric("Confidence score", f"{confidence.get('score', 0.0):.2f}")
    c3.metric("Evidence count", confidence.get("evidence_count", 0))

    if "_cache" in payload:
        st.caption(f"Loaded from intelligence cache: {payload['_cache'].get('profile_key')}")


def render_summary(payload: dict) -> None:
    """Render readable summary."""
    summary = payload.get("summary", {})

    st.markdown("## Intelligence Summary")
    st.info(summary.get("headline", ""))

    st.markdown("### Population")
    st.write(summary.get("population", ""))

    st.markdown("### Statistics")
    st.write(summary.get("statistics", ""))

    st.markdown("### Topology")
    st.write(summary.get("topology", ""))

    st.markdown("### Confidence")
    st.write(summary.get("confidence", ""))


def render_population(payload: dict) -> None:
    """Render population section."""
    population = payload.get("population_position")

    if not population:
        st.info("No population position available.")
        return

    c1, c2 = st.columns(2)
    c1.metric("Outlier rank", population.get("outlier_rank"))
    centroid_distance = population.get("centroid_distance")
    c2.metric("Centroid distance", "n/a" if centroid_distance is None else f"{centroid_distance:.3f}")

    st.markdown("### Nearest Neighbors")
    st.dataframe(population.get("nearest_neighbors", []), use_container_width=True)


def render_statistics(payload: dict) -> None:
    """Render statistics section."""
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
    """Render topology section."""
    topology = payload.get("topology_position")

    if not topology:
        st.info("No topology position available.")
        return

    if not topology.get("available"):
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
    """Render evidence section."""
    st.markdown("## Evidence")
    st.dataframe(payload.get("evidence", []), use_container_width=True)

    st.markdown("## Confidence")
    st.json(payload.get("confidence", {}))


def render_raw(payload: dict) -> None:
    """Render raw payload and download."""
    st.json(payload)

    st.download_button(
        "Download intelligence_payload.json",
        data=json.dumps(payload, indent=2, sort_keys=True),
        file_name="intelligence_payload.json",
        mime="application/json",
    )