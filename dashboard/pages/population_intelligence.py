"""Population Intelligence dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.population_intelligence_service import (
    DEFAULT_PROFILE_DIR,
    build_cluster_rows,
    build_neighbor_payload,
    build_population_intelligence_payload,
    collect_population_identities,
    json_export,
    slugify,
)


def render_population_intelligence_page() -> None:
    """Render Population Intelligence dashboard."""
    st.header("Population Intelligence")
    st.caption("Similarity, nearest neighbors, graph structure, and clustering.")

    profile_dir = st.text_input(
        "Profile library directory",
        value=str(DEFAULT_PROFILE_DIR),
    )

    threshold = st.slider(
        "Similarity graph threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.85,
        step=0.01,
    )

    with st.spinner("Building population intelligence payload..."):
        payload = build_population_intelligence_payload(
            profile_dir,
            threshold=threshold,
        )

    if not payload.get("success"):
        for error in payload.get("errors", []):
            st.error(error)
        with st.expander("Raw service payload", expanded=False):
            st.json(payload)
        return

    data = payload["data"]
    matrix = data["matrix"]
    graph = data["graph"]
    clusters = data["clusters"]

    render_summary_cards(payload)
    render_cluster_table(clusters)
    render_neighbor_explorer(matrix)
    render_downloads(data)


def render_summary_cards(payload: dict) -> None:
    """Render top-level population intelligence cards."""
    st.markdown("## Summary")

    metrics = payload.get("metrics", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Profiles", metrics.get("profiles", 0))
    c2.metric("Similarity Pairs", metrics.get("similarity_pairs", 0))
    c3.metric("Graph Edges", metrics.get("graph_edges", 0))
    c4.metric("Clusters", metrics.get("clusters", 0))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Mean Similarity", round(metrics.get("mean_similarity", 0.0), 4))
    c6.metric("Graph Density", round(metrics.get("graph_density", 0.0), 4))
    c7.metric("Largest Cluster", metrics.get("largest_cluster", 0))
    c8.metric("Singletons", metrics.get("singletons", 0))

    data = payload.get("data", {})

    with st.expander("Similarity Summary", expanded=False):
        st.json(getattr(data.get("matrix"), "summary", {}))

    with st.expander("Population Graph Summary", expanded=False):
        st.json(getattr(data.get("graph"), "summary", {}))

    with st.expander("Structural Clustering Summary", expanded=False):
        st.json(getattr(data.get("clusters"), "summary", {}))

    with st.expander("Raw Service Payload Metadata", expanded=False):
        st.json(
            {
                "success": payload.get("success"),
                "profile_dir": payload.get("profile_dir"),
                "threshold": payload.get("threshold"),
                "warnings": payload.get("warnings", []),
                "errors": payload.get("errors", []),
                "metrics": metrics,
            }
        )


def render_cluster_table(clusters) -> None:
    """Render structural cluster table."""
    st.markdown("## Structural Families")

    rows = build_cluster_rows(clusters)
    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        st.info("No structural clusters found.")
        return

    st.dataframe(
        dataframe,
        width="stretch",
    )

    st.download_button(
        label="Download clusters CSV",
        data=dataframe.to_csv(index=False),
        file_name="structural_clusters.csv",
        mime="text/csv",
    )


def render_neighbor_explorer(matrix) -> None:
    """Render nearest-neighbor explorer."""
    st.markdown("## Nearest Neighbor Explorer")

    identities = collect_population_identities(matrix)

    if not identities:
        st.info("No identities available.")
        return

    selected = st.selectbox(
        "Select profile",
        identities,
    )

    max_limit = min(25, max(1, len(identities) - 1))

    limit = st.slider(
        "Neighbor limit",
        min_value=1,
        max_value=max_limit,
        value=min(10, max_limit),
        step=1,
    )

    neighbor_payload = build_neighbor_payload(
        matrix,
        selected,
        limit=limit,
    )

    st.markdown(f"### Nearest Neighbors for {selected}")

    neighbors = neighbor_payload.get("neighbors", [])

    if neighbors:
        st.dataframe(
            pd.DataFrame(neighbors),
            width="stretch",
        )
    else:
        st.info("No neighbors found.")

    with st.expander("Neighbor Report JSON", expanded=False):
        st.json(neighbor_payload.get("report", {}))

    st.download_button(
        label="Download selected neighbor report JSON",
        data=json_export(neighbor_payload.get("report", {})),
        file_name=f"{slugify(selected)}_neighbors.json",
        mime="application/json",
    )


def render_downloads(data: dict) -> None:
    """Render JSON export buttons."""
    st.markdown("## Exports")

    c1, c2, c3 = st.columns(3)

    c1.download_button(
        label="Download similarity matrix JSON",
        data=json_export(data.get("matrix_dict", {})),
        file_name="similarity_matrix.json",
        mime="application/json",
    )

    c2.download_button(
        label="Download population graph JSON",
        data=json_export(data.get("graph_dict", {})),
        file_name="population_graph.json",
        mime="application/json",
    )

    c3.download_button(
        label="Download structural clusters JSON",
        data=json_export(data.get("clusters_dict", {})),
        file_name="structural_clusters.json",
        mime="application/json",
    )
