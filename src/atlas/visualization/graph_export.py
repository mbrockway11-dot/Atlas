"""Canonical Identity Graph visualization helpers."""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go

from atlas.visualization.graph_layout import circular_layout, layered_layout


def build_canonical_graph_figure(
    graph: dict[str, Any],
    *,
    title: str = "Canonical Identity Graph",
    layout: str = "layered",
) -> go.Figure:
    """Build a Plotly figure for an Atlas graph-like object."""
    positions = (
        circular_layout(graph)
        if layout == "circular"
        else layered_layout(graph)
    )

    edge_x: list[float | None] = []
    edge_y: list[float | None] = []

    for edge in graph.get("edges", {}).values():
        source = str(edge.get("source"))
        target = str(edge.get("target"))

        if source not in positions or target not in positions:
            continue

        x0, y0 = positions[source]
        x1, y1 = positions[target]

        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line={
            "width": 1,
        },
        hoverinfo="none",
        name="Edges",
    )

    node_x: list[float] = []
    node_y: list[float] = []
    node_size: list[float] = []
    node_color: list[float] = []
    node_text: list[str] = []

    for node_id, node in sorted(graph.get("nodes", {}).items()):
        if node_id not in positions:
            continue

        x, y = positions[node_id]
        coherence = float(node.get("coherence", {}).get("score", 0.0))
        truth = float(node.get("truth", {}).get("score", coherence))
        weight = float(node.get("weight", 1.0))

        node_x.append(x)
        node_y.append(y)
        node_size.append(10.0 + weight * 2.0 + truth * 20.0)
        node_color.append(truth)

        node_text.append(
            "<br>".join(
                [
                    f"node: {node_id}",
                    f"weight: {node.get('weight', 0)}",
                    f"degree: {node.get('degree', 0)}",
                    f"cipher_count: {node.get('cipher_count', 0)}",
                    f"planet_count: {node.get('planet_count', 0)}",
                    f"coherence: {coherence:.4f}",
                    f"truth: {truth:.4f}",
                    f"is_hub: {node.get('is_hub', False)}",
                    f"is_articulation: {node.get('is_articulation', False)}",
                    f"is_leaf: {node.get('is_leaf', False)}",
                ]
            )
        )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=[
            str(node_id)
            for node_id in sorted(graph.get("nodes", {}))
            if node_id in positions
        ],
        textposition="top center",
        hovertext=node_text,
        hoverinfo="text",
        marker={
            "size": node_size,
            "color": node_color,
            "colorscale": "Viridis",
            "showscale": True,
            "colorbar": {
                "title": "Truth",
            },
            "line": {
                "width": 1,
            },
        },
        name="Nodes",
    )

    figure = go.Figure(data=[edge_trace, node_trace])

    figure.update_layout(
        title=title,
        showlegend=False,
        hovermode="closest",
        margin={
            "b": 20,
            "l": 20,
            "r": 20,
            "t": 50,
        },
        xaxis={
            "showgrid": False,
            "zeroline": False,
            "showticklabels": False,
        },
        yaxis={
            "showgrid": False,
            "zeroline": False,
            "showticklabels": False,
        },
    )

    return figure
