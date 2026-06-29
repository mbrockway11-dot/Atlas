"""Population Intelligence dashboard page."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from atlas.calibration.nearest_neighbor import (
    find_nearest_neighbors,
    neighbor_result_to_dict,
)
from atlas.calibration.population_graph import (
    build_population_graph,
    population_graph_to_dict,
)
from atlas.calibration.similarity_matrix import (
    build_similarity_matrix_from_library,
    similarity_matrix_to_dict,
)
from atlas.calibration.structural_clustering import (
    build_structural_clusters,
    structural_clustering_result_to_dict,
)


DEFAULT_PROFILE_DIR = Path("output/library/profiles")


def render_population_intelligence_page() -> None:
    """Render Population Intelligence dashboard."""
    st.header("Population Intelligence")
    st.caption("Similarity, nearest neighbors, graph structure, and clustering.")

    profile_dir = st.text_input(
        "Profile library directory",
        value=str(DEFAULT_PROFILE_DIR),
    )

    root = Path(profile_dir)

    if not root.exists():
        st.error(f"Profile directory not found: {root}")
        return

    threshold = st.slider(
        "Similarity graph threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.85,
        step=0.01,
    )

    with st.spinner("Building similarity matrix, population graph, and clusters..."):
        matrix = build_similarity_matrix_from_library(root)
        graph = build_population_graph(matrix, threshold=threshold)
        clusters = build_structural_clusters(graph)

    render_summary_cards(matrix, graph, clusters)
    render_cluster_table(clusters)
    render_neighbor_explorer(matrix)
    render_downloads(matrix, graph, clusters)


def render_summary_cards(matrix, graph, clusters) -> None:
    """Render top-level population intelligence cards."""
    st.markdown("## Summary")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Profiles", matrix.profile_count)
    c2.metric("Similarity Pairs", matrix.pair_count)
    c3.metric("Graph Edges", graph.edge_count)
    c4.metric("Clusters", clusters.cluster_count)

    c5, c6, c7, c8 = st.columns(4)

    c5.metric(
        "Mean Similarity",
        round(matrix.summary.get("mean_similarity", 0.0), 4),
    )
    c6.metric(
        "Graph Density",
        round(graph.summary.get("density", 0.0), 4),
    )
    c7.metric(
        "Largest Cluster",
        clusters.summary.get("largest_cluster_size", 0),
    )
    c8.metric(
        "Singletons",
        clusters.singleton_count,
    )

    with st.expander("Similarity Summary", expanded=False):
        st.json(matrix.summary)

    with st.expander("Population Graph Summary", expanded=False):
        st.json(graph.summary)

    with st.expander("Structural Clustering Summary", expanded=False):
        st.json(clusters.summary)


def render_cluster_table(clusters) -> None:
    """Render structural cluster table."""
    st.markdown("## Structural Families")

    rows = []

    for cluster in clusters.clusters:
        rows.append(
            {
                "cluster_id": cluster.cluster_id,
                "member_count": cluster.member_count,
                "internal_edge_count": cluster.internal_edge_count,
                "average_internal_similarity": cluster.average_internal_similarity,
                "members": ", ".join(cluster.members),
                "strongest_pair": format_strongest_pair(cluster.strongest_pair),
            }
        )

    dataframe = pd.DataFrame(rows)

    st.dataframe(
        dataframe,
        use_container_width=True,
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

    identities = collect_matrix_identities(matrix)

    if not identities:
        st.info("No identities available.")
        return

    selected = st.selectbox(
        "Select profile",
        identities,
    )

    limit = st.slider(
        "Neighbor limit",
        min_value=1,
        max_value=min(25, max(1, len(identities) - 1)),
        value=min(10, max(1, len(identities) - 1)),
        step=1,
    )

    neighbors = find_nearest_neighbors(
        matrix,
        selected,
        limit=limit,
    )

    st.markdown(f"### Nearest Neighbors for {selected}")

    if neighbors.neighbors:
        st.dataframe(
            pd.DataFrame(neighbors.neighbors),
            use_container_width=True,
        )
    else:
        st.info("No neighbors found.")

    with st.expander("Neighbor Report JSON", expanded=False):
        st.json(neighbor_result_to_dict(neighbors))

    st.download_button(
        label="Download selected neighbor report JSON",
        data=json.dumps(
            neighbor_result_to_dict(neighbors),
            indent=2,
            sort_keys=True,
        ),
        file_name=f"{slugify(selected)}_neighbors.json",
        mime="application/json",
    )


def render_downloads(matrix, graph, clusters) -> None:
    """Render JSON export buttons."""
    st.markdown("## Exports")

    c1, c2, c3 = st.columns(3)

    c1.download_button(
        label="Download similarity matrix JSON",
        data=json.dumps(
            similarity_matrix_to_dict(matrix),
            indent=2,
            sort_keys=True,
        ),
        file_name="similarity_matrix.json",
        mime="application/json",
    )

    c2.download_button(
        label="Download population graph JSON",
        data=json.dumps(
            population_graph_to_dict(graph),
            indent=2,
            sort_keys=True,
        ),
        file_name="population_graph.json",
        mime="application/json",
    )

    c3.download_button(
        label="Download structural clusters JSON",
        data=json.dumps(
            structural_clustering_result_to_dict(clusters),
            indent=2,
            sort_keys=True,
        ),
        file_name="structural_clusters.json",
        mime="application/json",
    )


def collect_matrix_identities(matrix) -> list[str]:
    """Collect identities represented in a similarity matrix."""
    identities: set[str] = set()

    for result in matrix.results:
        identities.add(result.identity_a)
        identities.add(result.identity_b)

    return sorted(identities)


def format_strongest_pair(pair) -> str:
    """Format strongest pair display."""
    if not pair:
        return ""

    return (
        f"{pair['identity_a']} ↔ {pair['identity_b']} "
        f"({round(pair['similarity'], 4)})"
    )


def slugify(value: str) -> str:
    """Build safe filename slug."""
    return (
        value.casefold()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )