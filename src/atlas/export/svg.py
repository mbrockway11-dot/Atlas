"""SVG export utilities for topology graphs."""

from pathlib import Path

from atlas.topology.graph import Edge, Node, TopologyGraph


def export_graph_svg(
    graph: TopologyGraph,
    output_path: str | Path,
    grid_size: int,
    canvas_size: int = 600,
    padding: int = 60,
) -> Path:
    """Export a topology graph as a deterministic 2D SVG."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    svg = graph_to_svg(
        graph=graph,
        grid_size=grid_size,
        canvas_size=canvas_size,
        padding=padding,
    )

    path.write_text(svg, encoding="utf-8")

    return path


def export_graph_svg_3d(
    graph: TopologyGraph,
    output_path: str | Path,
    grid_size: int,
    canvas_size: int = 700,
    padding: int = 80,
    depth_offset: float = 4.0,
) -> Path:
    """Export a topology graph as a deterministic pseudo-3D SVG."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    svg = graph_to_svg_3d(
        graph=graph,
        grid_size=grid_size,
        canvas_size=canvas_size,
        padding=padding,
        depth_offset=depth_offset,
    )

    path.write_text(svg, encoding="utf-8")

    return path


def graph_to_svg(
    graph: TopologyGraph,
    grid_size: int,
    canvas_size: int = 600,
    padding: int = 60,
) -> str:
    """Convert a topology graph to 2D SVG text."""
    if grid_size <= 0:
        raise ValueError("grid_size must be greater than zero.")

    coordinate_map = {
        node: _node_to_canvas_point(
            node=node,
            grid_size=grid_size,
            canvas_size=canvas_size,
            padding=padding,
        )
        for node in graph.nodes
    }

    lines = [
        _svg_header(canvas_size),
        _svg_background(canvas_size),
    ]

    for edge in graph.edges:
        lines.append(_edge_svg(edge, graph, coordinate_map))

    for node in graph.nodes:
        lines.append(_node_svg(node, graph, coordinate_map))

    lines.append("</svg>")

    return "\n".join(lines)


def graph_to_svg_3d(
    graph: TopologyGraph,
    grid_size: int,
    canvas_size: int = 700,
    padding: int = 80,
    depth_offset: float = 4.0,
) -> str:
    """Convert a topology graph to pseudo-3D SVG text.

    Repeated nodes are visualized as stacked depth layers.
    Repeated edges are visualized with thicker shadowed paths.
    """
    if grid_size <= 0:
        raise ValueError("grid_size must be greater than zero.")

    coordinate_map = {
        node: _node_to_canvas_point(
            node=node,
            grid_size=grid_size,
            canvas_size=canvas_size,
            padding=padding,
        )
        for node in graph.nodes
    }

    lines = [
        _svg_header(canvas_size),
        _svg_defs(),
        _svg_background(canvas_size),
        '<g id="edges-3d">',
    ]

    for edge in graph.edges:
        lines.append(_edge_svg_3d(edge, graph, coordinate_map, depth_offset))

    lines.append("</g>")
    lines.append('<g id="nodes-3d">')

    for node in graph.nodes:
        lines.append(_node_svg_3d(node, graph, coordinate_map, depth_offset))

    lines.append("</g>")
    lines.append("</svg>")

    return "\n".join(lines)


def _node_to_canvas_point(
    node: Node,
    grid_size: int,
    canvas_size: int,
    padding: int,
) -> tuple[float, float]:
    """Map a graph node row/col coordinate to SVG x/y space."""
    row, col = node

    drawable = canvas_size - (padding * 2)

    if grid_size == 1:
        return canvas_size / 2, canvas_size / 2

    step = drawable / (grid_size - 1)

    x = padding + (col * step)
    y = padding + (row * step)

    return x, y


def _svg_header(canvas_size: int) -> str:
    """Return SVG header."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{canvas_size}" height="{canvas_size}" '
        f'viewBox="0 0 {canvas_size} {canvas_size}">'
    )


def _svg_defs() -> str:
    """Return SVG defs for pseudo-3D rendering."""
    return (
        "<defs>\n"
        '  <filter id="soft-shadow" x="-30%" y="-30%" width="160%" height="160%">\n'
        '    <feDropShadow dx="4" dy="6" stdDeviation="4" flood-opacity="0.35"/>\n'
        "  </filter>\n"
        '  <linearGradient id="node-gradient" x1="0%" y1="0%" x2="100%" y2="100%">\n'
        '    <stop offset="0%" stop-color="white"/>\n'
        '    <stop offset="100%" stop-color="#d9d9d9"/>\n'
        "  </linearGradient>\n"
        "</defs>"
    )


def _svg_background(canvas_size: int) -> str:
    """Return SVG background."""
    return (
        f'<rect x="0" y="0" width="{canvas_size}" height="{canvas_size}" '
        f'fill="white" />'
    )


def _edge_svg(
    edge: Edge,
    graph: TopologyGraph,
    coordinate_map: dict[Node, tuple[float, float]],
) -> str:
    """Return SVG line for one 2D edge."""
    source, target = edge
    x1, y1 = coordinate_map[source]
    x2, y2 = coordinate_map[target]

    weight = graph.edge_weights.get(edge, 1)
    stroke_width = _edge_stroke_width(weight)

    return (
        f'<line x1="{x1:.2f}" y1="{y1:.2f}" '
        f'x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="black" stroke-width="{stroke_width:.2f}" '
        f'stroke-linecap="round" opacity="0.65" />'
    )


def _edge_svg_3d(
    edge: Edge,
    graph: TopologyGraph,
    coordinate_map: dict[Node, tuple[float, float]],
    depth_offset: float,
) -> str:
    """Return SVG lines for one pseudo-3D edge."""
    source, target = edge
    x1, y1 = coordinate_map[source]
    x2, y2 = coordinate_map[target]

    weight = graph.edge_weights.get(edge, 1)
    stroke_width = _edge_stroke_width(weight)

    shadow_offset = depth_offset * min(weight, 6)

    return (
        f'<g class="edge-3d" data-weight="{weight}">\n'
        f'  <line x1="{x1 + shadow_offset:.2f}" y1="{y1 + shadow_offset:.2f}" '
        f'x2="{x2 + shadow_offset:.2f}" y2="{y2 + shadow_offset:.2f}" '
        f'stroke="#999999" stroke-width="{stroke_width:.2f}" '
        f'stroke-linecap="round" opacity="0.35" />\n'
        f'  <line x1="{x1:.2f}" y1="{y1:.2f}" '
        f'x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="black" stroke-width="{stroke_width:.2f}" '
        f'stroke-linecap="round" opacity="0.75" />\n'
        f"</g>"
    )


def _node_svg(
    node: Node,
    graph: TopologyGraph,
    coordinate_map: dict[Node, tuple[float, float]],
) -> str:
    """Return SVG circle for one 2D node."""
    x, y = coordinate_map[node]

    weight = graph.node_weights.get(node, 1)
    radius = _node_radius(weight)

    return (
        f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.2f}" '
        f'fill="white" stroke="black" stroke-width="2" />'
    )


def _node_svg_3d(
    node: Node,
    graph: TopologyGraph,
    coordinate_map: dict[Node, tuple[float, float]],
    depth_offset: float,
) -> str:
    """Return SVG stacked circles for one pseudo-3D node."""
    x, y = coordinate_map[node]

    weight = graph.node_weights.get(node, 1)
    radius = _node_radius(weight)
    depth_layers = max(1, min(weight, 8))

    lines = [f'<g class="node-3d" data-weight="{weight}" filter="url(#soft-shadow)">']

    for layer in range(depth_layers, 0, -1):
        offset = layer * depth_offset
        lines.append(
            f'  <circle cx="{x + offset:.2f}" cy="{y + offset:.2f}" '
            f'r="{radius:.2f}" fill="#cfcfcf" '
            f'stroke="#666666" stroke-width="1" opacity="0.45" />'
        )

    lines.append(
        f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.2f}" '
        f'fill="url(#node-gradient)" stroke="black" stroke-width="2.5" />'
    )

    lines.append("</g>")

    return "\n".join(lines)


def _node_radius(weight: int) -> float:
    """Scale node radius by weight."""
    return 6.0 + max(0, weight - 1) * 3.0


def _edge_stroke_width(weight: int) -> float:
    """Scale edge stroke width by weight."""
    return 1.5 + max(0, weight - 1) * 1.5