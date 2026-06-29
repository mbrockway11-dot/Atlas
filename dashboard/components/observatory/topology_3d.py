"""3D topology Observatory component."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from atlas.visualization.topology_3d import (
    build_3d_topology_edges,
    build_3d_topology_points,
)


def render_3d_topology_view(acf: dict) -> None:
    """Render interactive 3D topology."""
    st.markdown("## 3D Identity Topology")

    z_mode = st.selectbox(
        "Z-axis mode",
        [
            "visit_depth",
            "sequence_order",
            "planet_stack",
        ],
    )

    selected_ciphers = st.multiselect(
        "Ciphers",
        [
            "ordinal",
            "hebrew_literal",
            "hebrew_phonetic",
        ],
        default=[
            "ordinal",
            "hebrew_literal",
            "hebrew_phonetic",
        ],
    )

    selected_planets = st.multiselect(
        "Planets",
        [
            "Saturn",
            "Jupiter",
            "Mars",
            "Sun",
            "Venus",
            "Mercury",
            "Moon",
        ],
        default=[
            "Saturn",
            "Jupiter",
            "Mars",
            "Sun",
            "Venus",
            "Mercury",
            "Moon",
        ],
    )

    points = [
        point
        for point in build_3d_topology_points(acf, z_mode=z_mode)
        if point["cipher"] in selected_ciphers
        and point["planet"] in selected_planets
    ]

    edges = [
        edge
        for edge in build_3d_topology_edges(acf, z_mode=z_mode)
        if edge["cipher"] in selected_ciphers
        and edge["planet"] in selected_planets
    ]

    figure = build_figure(points, edges)

    st.plotly_chart(
        figure,
        use_container_width=True,
    )

    with st.expander("3D point data"):
        st.dataframe(
            pd.DataFrame(points),
            use_container_width=True,
        )


def build_figure(
    points: list[dict],
    edges: list[dict],
) -> go.Figure:
    """Build Plotly 3D figure."""
    figure = go.Figure()

    for edge in edges:
        figure.add_trace(
            go.Scatter3d(
                x=edge["x"],
                y=edge["y"],
                z=edge["z"],
                mode="lines",
                line={
                    "color": edge["color"],
                    "width": 3,
                },
                opacity=0.25,
                showlegend=False,
                hoverinfo="skip",
            )
        )

    if points:
        figure.add_trace(
            go.Scatter3d(
                x=[point["x"] for point in points],
                y=[point["y"] for point in points],
                z=[point["z"] for point in points],
                mode="markers",
                marker={
                    "size": 5,
                    "color": [point["color"] for point in points],
                    "opacity": 0.82,
                },
                text=[
                    (
                        f"{point['layer_id']}<br>"
                        f"Node: {point['node']}<br>"
                        f"Planet: {point['planet']}<br>"
                        f"Cipher: {point['cipher']}<br>"
                        f"Visit depth: {point['visit_depth']}<br>"
                        f"Sequence: {point['sequence_index']}"
                    )
                    for point in points
                ],
                hoverinfo="text",
                name="Visits",
            )
        )

    figure.update_layout(
        height=760,
        margin={
            "l": 0,
            "r": 0,
            "t": 30,
            "b": 0,
        },
        scene={
            "xaxis_title": "Kamea X",
            "yaxis_title": "Kamea Y",
            "zaxis_title": "Depth / Time",
            "aspectmode": "cube",
        },
        template="plotly_dark",
    )

    return figure