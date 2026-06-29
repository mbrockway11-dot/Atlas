"""Population Topology dashboard page."""

from __future__ import annotations

from pathlib import Path
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles
from atlas.research.matrix import build_profile_matrix_rows
from atlas.research.population_topology import (
    build_population_topology_graph,
    population_topology_report_to_json,
    topology_edges_dataframe,
    topology_nodes_dataframe,
)
from atlas.research.statistical import principal_components
from atlas.research.validation import build_profile_feature_matrix, load_cohort_index

DEFAULT_COHORT_INDEX = Path("research/profile_intake/cohort_index.csv")


def render_population_topology_page() -> None:
    """Render population-level topology graph."""
    st.header("Population Topology")
    st.caption(
        "Graph the full profile population as a similarity network. This extends "
        "the existing single-profile topology system to the corpus scale."
    )

    matrix = load_profile_library_matrix()
    if matrix.empty:
        st.error("No profile matrix rows could be loaded from the profile library.")
        return

    profile_features = build_profile_feature_matrix(matrix)
    if profile_features.empty or len(profile_features) < 2:
        st.error("At least two profiles are required for population topology.")
        return

    controls = st.columns(4)
    metric = controls[0].radio("Similarity metric", ["cosine", "euclidean"], horizontal=True)
    threshold = controls[1].slider("Edge threshold", 0.0, 1.0, 0.75, 0.01)
    top_k = controls[2].slider("Minimum top-k neighbors", 0, min(20, len(profile_features) - 1), min(5, len(profile_features) - 1))
    layout_mode = controls[3].radio("Layout", ["PCA", "Circle"], horizontal=True)

    cohort_path = st.text_input("Optional cohort index CSV", value=str(DEFAULT_COHORT_INDEX))
    cohort_index = load_cohort_index(cohort_path)

    graph = build_population_topology_graph(
        profile_features,
        threshold=threshold,
        top_k=top_k,
        metric=metric,
    )

    if not cohort_index.empty:
        attach_cohorts(graph, cohort_index)

    render_summary(graph)

    tab_graph, tab_nodes, tab_edges, tab_components, tab_communities, tab_exports = st.tabs(
        ["Graph", "Nodes", "Edges", "Components", "Communities", "Exports"]
    )

    with tab_graph:
        render_graph(graph, profile_features, layout_mode)

    with tab_nodes:
        render_nodes(graph)

    with tab_edges:
        render_edges(graph)

    with tab_components:
        render_components(graph)

    with tab_communities:
        render_communities(graph)

    with tab_exports:
        render_exports(graph)


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
        except Exception as exc:  # pragma: no cover - dashboard safety
            st.warning(f"Skipped {profile_key}: {exc}")

    return pd.DataFrame(rows)


def attach_cohorts(graph: dict, cohort_index: pd.DataFrame) -> None:
    """Attach optional cohort labels to graph nodes."""
    cohort_map = dict(zip(cohort_index["name"].astype(str), cohort_index["cohort"].astype(str), strict=False))
    for node_id, node in graph["nodes"].items():
        node["cohort"] = cohort_map.get(node_id, "")


def render_summary(graph: dict) -> None:
    """Render summary metrics."""
    summary = graph["summary"]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Profiles", graph["node_count"])
    c2.metric("Edges", graph["edge_count"])
    c3.metric("Density", f"{summary['density']:.3f}")
    c4.metric("Components", summary["component_count"])
    c5.metric("Communities", summary["community_count"])


def render_graph(graph: dict, profile_features: pd.DataFrame, layout_mode: str) -> None:
    """Render interactive population topology graph."""
    st.markdown("## Population Similarity Network")
    positions = build_positions(graph, profile_features, layout_mode)
    figure = build_network_figure(graph, positions)
    st.plotly_chart(figure, use_container_width=True)

    st.markdown("### Most Connected Profiles")
    st.dataframe(pd.DataFrame(graph["summary"]["most_connected_profiles"]), use_container_width=True)


def build_positions(graph: dict, profile_features: pd.DataFrame, layout_mode: str) -> dict[str, dict[str, float]]:
    """Build deterministic 2D node positions."""
    names = sorted(graph["nodes"])

    if layout_mode == "PCA":
        pca = principal_components(profile_features, n_components=2)
        if pca["available"]:
            positions = {}
            for row in pca["coordinates"]:
                positions[row["name"]] = {
                    "x": float(row.get("pc1", 0.0)),
                    "y": float(row.get("pc2", 0.0)),
                }
            return positions

    positions = {}
    count = max(len(names), 1)
    for index, name in enumerate(names):
        angle = 2.0 * 3.141592653589793 * index / count
        positions[name] = {"x": float(np_cos(angle)), "y": float(np_sin(angle))}
    return positions


def np_cos(value: float) -> float:
    """Small wrapper to avoid importing numpy in dashboard page."""
    import math

    return math.cos(value)


def np_sin(value: float) -> float:
    """Small wrapper to avoid importing numpy in dashboard page."""
    import math

    return math.sin(value)


def build_network_figure(graph: dict, positions: dict[str, dict[str, float]]) -> go.Figure:
    """Build Plotly network figure."""
    figure = go.Figure()

    for edge in graph["edges"].values():
        source = edge["source"]
        target = edge["target"]
        if source not in positions or target not in positions:
            continue

        figure.add_trace(
            go.Scatter(
                x=[positions[source]["x"], positions[target]["x"], None],
                y=[positions[source]["y"], positions[target]["y"], None],
                mode="lines",
                line={"width": max(1, min(float(edge["weight"]) * 5, 6)), "color": "#64748b"},
                opacity=0.25,
                hoverinfo="skip",
                showlegend=False,
            )
        )

    nodes = list(graph["nodes"].values())
    if nodes:
        figure.add_trace(
            go.Scatter(
                x=[positions[node["id"]]["x"] for node in nodes],
                y=[positions[node["id"]]["y"] for node in nodes],
                mode="markers+text",
                marker={
                    "size": [max(8, min(28, 8 + float(node.get("weighted_degree", 0.0)))) for node in nodes],
                    "color": [int(node.get("community") or 0) for node in nodes],
                    "opacity": 0.9,
                    "showscale": True,
                    "colorbar": {"title": "Community"},
                },
                text=[node["label"] for node in nodes],
                textposition="top center",
                hovertext=[node_hover_text(node) for node in nodes],
                hoverinfo="text",
                name="Profiles",
            )
        )

    figure.update_layout(
        height=760,
        template="plotly_dark",
        margin={"l": 0, "r": 0, "t": 35, "b": 0},
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    return figure


def node_hover_text(node: dict) -> str:
    """Build node hover text."""
    return (
        f"Profile: {node['label']}<br>"
        f"Degree: {node.get('degree', 0)}<br>"
        f"Weighted degree: {node.get('weighted_degree', 0.0):.3f}<br>"
        f"Degree centrality: {node.get('degree_centrality', 0.0):.3f}<br>"
        f"Closeness: {node.get('closeness_centrality', 0.0):.3f}<br>"
        f"Component: {node.get('component')}<br>"
        f"Community: {node.get('community')}<br>"
        f"Cohort: {node.get('cohort', '')}"
    )


def render_nodes(graph: dict) -> None:
    """Render node table."""
    st.markdown("## Nodes / Profile Centrality")
    nodes = topology_nodes_dataframe(graph)
    if not nodes.empty:
        nodes = nodes.sort_values(by=["weighted_degree", "degree", "id"], ascending=[False, False, True])
    st.dataframe(nodes, use_container_width=True)


def render_edges(graph: dict) -> None:
    """Render edge table."""
    st.markdown("## Edges / Similarity Links")
    edges = topology_edges_dataframe(graph)
    if not edges.empty:
        edges = edges.sort_values(by=["similarity", "source", "target"], ascending=[False, True, True])
    st.dataframe(edges, use_container_width=True)


def render_components(graph: dict) -> None:
    """Render connected components."""
    st.markdown("## Connected Components")
    st.dataframe(pd.DataFrame(graph["components"]), use_container_width=True)


def render_communities(graph: dict) -> None:
    """Render detected communities."""
    st.markdown("## Communities")
    st.caption("Deterministic weighted label-propagation communities over the similarity graph.")
    st.dataframe(pd.DataFrame(graph["communities"]), use_container_width=True)


def render_exports(graph: dict) -> None:
    """Render export controls."""
    st.markdown("## Exports")
    st.download_button(
        "Download population_topology_graph.json",
        data=population_topology_report_to_json(graph),
        file_name="population_topology_graph.json",
        mime="application/json",
    )

    nodes = topology_nodes_dataframe(graph)
    st.download_button(
        "Download population_topology_nodes.csv",
        data=nodes.to_csv(index=False).encode("utf-8"),
        file_name="population_topology_nodes.csv",
        mime="text/csv",
    )

    edges = topology_edges_dataframe(graph)
    st.download_button(
        "Download population_topology_edges.csv",
        data=edges.to_csv(index=False).encode("utf-8"),
        file_name="population_topology_edges.csv",
        mime="text/csv",
    )