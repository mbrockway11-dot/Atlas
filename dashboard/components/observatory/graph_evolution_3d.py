"""Graph Evolution 3D component."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from atlas.graph import (
    analyze_identity_graph,
    build_identity_graph_v2,
    compute_coherence_field,
    reduce_identity_graph,
)


REGION_COLORS = {
    "core": "#facc15",
    "adaptive": "#38bdf8",
    "peripheral": "#64748b",
}


def render_graph_evolution_3d(acf: dict) -> None:
    """Render raw, analyzed, coherent, and reduced IdentityGraph states."""
    st.markdown("## Graph Evolution 3D")
    st.caption(
        "Inspect the single merged IdentityGraph as it moves from construction "
        "to analysis, coherence, and reduction."
    )

    raw = build_identity_graph_v2(acf)
    analyzed = analyze_identity_graph(raw)
    coherent = compute_coherence_field(raw)
    reduced = reduce_identity_graph(raw)

    state_name = st.radio(
        "Graph State",
        [
            "Raw IdentityGraph",
            "Analyzed Graph",
            "Coherence Field",
            "Reduced / Structural Attractor",
        ],
        horizontal=True,
    )

    graph = {
        "Raw IdentityGraph": raw,
        "Analyzed Graph": analyzed,
        "Coherence Field": coherent,
        "Reduced / Structural Attractor": reduced,
    }[state_name]

    z_mode = st.selectbox(
        "Z Axis",
        [
            "weight",
            "coherence",
            "degree",
            "construction_count",
        ],
    )

    figure = build_graph_figure(graph, z_mode)

    st.plotly_chart(figure, width="stretch")

    render_graph_summary(graph, state_name)

    with st.expander("Node Data"):
        st.dataframe(pd.DataFrame(graph["nodes"].values()), width="stretch")

    with st.expander("Edge Data"):
        st.dataframe(pd.DataFrame(graph["edges"].values()), width="stretch")


def build_graph_figure(graph: dict, z_mode: str) -> go.Figure:
    """Build Plotly 3D graph figure."""
    figure = go.Figure()

    node_positions = build_node_positions(graph, z_mode)

    for edge in graph["edges"].values():
        source = edge["source"]
        target = edge["target"]

        if source not in node_positions or target not in node_positions:
            continue

        source_pos = node_positions[source]
        target_pos = node_positions[target]

        figure.add_trace(
            go.Scatter3d(
                x=[source_pos["x"], target_pos["x"], None],
                y=[source_pos["y"], target_pos["y"], None],
                z=[source_pos["z"], target_pos["z"], None],
                mode="lines",
                line={
                    "width": max(1, min(edge.get("weight", 1), 8)),
                    "color": "#94a3b8",
                },
                opacity=0.35,
                hoverinfo="skip",
                showlegend=False,
            )
        )

    nodes = list(graph["nodes"].values())

    if nodes:
        figure.add_trace(
            go.Scatter3d(
                x=[node_positions[node["id"]]["x"] for node in nodes],
                y=[node_positions[node["id"]]["y"] for node in nodes],
                z=[node_positions[node["id"]]["z"] for node in nodes],
                mode="markers+text",
                marker={
                    "size": [
                        max(4, min(node.get("weight", 1) * 2, 18))
                        for node in nodes
                    ],
                    "color": [node_color(node) for node in nodes],
                    "opacity": 0.9,
                },
                text=[node["id"] for node in nodes],
                textposition="top center",
                hovertext=[node_hover_text(node) for node in nodes],
                hoverinfo="text",
                name="Nodes",
            )
        )

    figure.update_layout(
        height=760,
        template="plotly_dark",
        margin={"l": 0, "r": 0, "t": 35, "b": 0},
        scene={
            "xaxis_title": "X",
            "yaxis_title": "Y",
            "zaxis_title": z_mode,
            "aspectmode": "cube",
        },
    )

    return figure


def build_node_positions(graph: dict, z_mode: str) -> dict[str, dict]:
    """Build 3D positions for graph nodes."""
    positions = {}

    for index, node in enumerate(graph["nodes"].values()):
        coordinate = node.get("coordinate_consensus")

        if coordinate:
            y, x = coordinate
        else:
            x = index % 10
            y = index // 10

        positions[node["id"]] = {
            "x": float(x),
            "y": float(y),
            "z": resolve_z(node, z_mode),
        }

    return positions


def resolve_z(node: dict, z_mode: str) -> float:
    """Resolve z-axis value."""
    if z_mode == "coherence":
        return float(node.get("coherence", {}).get("score", 0.0))

    if z_mode == "degree":
        return float(node.get("degree", 0))

    if z_mode == "construction_count":
        return float(node.get("construction_count", node.get("visit_count", 0)))

    return float(node.get("weight", 0))


def node_color(node: dict) -> str:
    """Resolve node color from coherence region."""
    region = node.get("coherence", {}).get("region")

    if region:
        return REGION_COLORS.get(region, "#ffffff")

    if node.get("is_articulation"):
        return "#f97316"

    if node.get("is_hub"):
        return "#22c55e"

    if node.get("is_leaf"):
        return "#64748b"

    return "#e2e8f0"


def node_hover_text(node: dict) -> str:
    """Build node hover label."""
    coherence = node.get("coherence", {})

    return (
        f"Node: {node['id']}<br>"
        f"Weight: {node.get('weight', 0)}<br>"
        f"Degree: {node.get('degree', 'n/a')}<br>"
        f"Ciphers: {node.get('cipher_count', 0)}<br>"
        f"Planets: {node.get('planet_count', 0)}<br>"
        f"Coherence: {coherence.get('score', 'n/a')}<br>"
        f"Region: {coherence.get('region', 'n/a')}"
    )


def render_graph_summary(graph: dict, state_name: str) -> None:
    """Render graph summary cards."""
    st.markdown(f"### {state_name}")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Nodes", len(graph["nodes"]))
    c2.metric("Edges", len(graph["edges"]))
    c3.metric("Passes", len(graph.get("construction_passes", [])))
    c4.metric("Version", graph.get("version", "n/a"))

    if "analysis" in graph:
        a1, a2, a3, a4 = st.columns(4)

        a1.metric("Components", graph["analysis"]["component_count"])
        a2.metric("Bridges", graph["analysis"]["bridge_count"])
        a3.metric("Articulations", graph["analysis"]["articulation_point_count"])
        a4.metric("Hubs", graph["analysis"]["hub_count"])

    if "coherence" in graph:
        k1, k2, k3 = st.columns(3)

        k1.metric("Core Nodes", graph["coherence"]["core_node_count"])
        k2.metric("Adaptive Nodes", graph["coherence"]["adaptive_node_count"])
        k3.metric("Peripheral Nodes", graph["coherence"]["peripheral_node_count"])

    if "reduction" in graph:
        r1, r2, r3, r4 = st.columns(4)

        r1.metric("Removed Nodes", graph["reduction"]["removed_node_count"])
        r2.metric("Removed Edges", graph["reduction"]["removed_edge_count"])
        r3.metric("Iterations", graph["reduction"]["iterations"])
        r4.metric("Converged", str(graph["reduction"]["converged"]))
