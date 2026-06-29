"""Planetary composite SVG renderer."""

from pathlib import Path
from typing import Any

from atlas.visualization.render_options import RenderOptions


CIPHER_STYLES = {
    "ordinal": {
        "stroke": "#d4af37",
        "label": "Ordinal",
    },
    "hebrew_literal": {
        "stroke": "#3b82f6",
        "label": "Hebrew Literal",
    },
    "hebrew_phonetic": {
        "stroke": "#8b5cf6",
        "label": "Hebrew Phonetic",
    },
}


def render_planetary_composite_svg(
    layers: list[dict[str, Any]],
    options: RenderOptions | None = None,
) -> str:
    """Render one planetary composite SVG from three cipher layers."""
    options = options or RenderOptions()

    if not layers:
        raise ValueError("At least one layer is required.")

    planet = layers[0]["planet"]
    grid_size = layers[0]["grid_size"]

    width = options.output_size
    height = options.output_size
    padding = options.padding
    usable = width - (padding * 2)
    step = usable / max(grid_size - 1, 1)

    svg_parts = [
        svg_header(width, height),
        background_rect(width, height),
        title_text(planet, width),
    ]

    if options.show_grid:
        svg_parts.append(render_grid(grid_size, padding, step))

    for layer in layers:
        svg_parts.append(render_layer_path(layer, padding, step, options))

    svg_parts.append(render_legend(layers, width, height))
    svg_parts.append("</svg>")

    return "\n".join(svg_parts)


def export_planetary_composite_svg(
    layers: list[dict[str, Any]],
    output_path: str | Path,
    options: RenderOptions | None = None,
) -> Path:
    """Export one planetary composite SVG."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    svg = render_planetary_composite_svg(layers, options)
    output_path.write_text(svg, encoding="utf-8")

    return output_path


def render_layer_path(
    layer: dict[str, Any],
    padding: int,
    step: float,
    options: RenderOptions,
) -> str:
    """Render one cipher layer path."""
    cipher = layer["cipher"]
    style = CIPHER_STYLES.get(
        cipher,
        {
            "stroke": "#ffffff",
            "label": cipher,
        },
    )

    path_views = layer["features"]["path_views"]
    visual_coordinates = path_views["render_path"]["coordinates"]
    visit_history = path_views["analysis_path"]["visit_history"]

    points = [
        coordinate_to_svg_point(coordinate, padding, step)
        for coordinate in visual_coordinates
    ]

    if not points:
        return ""

    parts = []

    point_string = " ".join(
        f"{x:.2f},{y:.2f}"
        for x, y in points
    )

    parts.append(
        (
            f'<polyline points="{point_string}" '
            f'fill="none" '
            f'stroke="{style["stroke"]}" '
            f'stroke-width="4" '
            f'stroke-opacity="0.72" '
            f'stroke-linecap="round" '
            f'stroke-linejoin="round" />'
        )
    )

    for coordinate in visual_coordinates:
        x, y = coordinate_to_svg_point(coordinate, padding, step)
        node_key = str(node_from_coordinate(layer, coordinate))
        depth = visit_history["node_weights"].get(node_key, 1)

        radius = 8 + (depth * 2 if options.show_visit_depth else 0)

        parts.append(
            (
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.2f}" '
                f'fill="{style["stroke"]}" '
                f'fill-opacity="0.45" '
                f'stroke="{style["stroke"]}" '
                f'stroke-width="2" />'
            )
        )

        if options.show_node_labels:
            parts.append(
                (
                    f'<text x="{x:.2f}" y="{y - radius - 6:.2f}" '
                    f'font-size="18" '
                    f'fill="#f8fafc" '
                    f'text-anchor="middle">{node_key}</text>'
                )
            )

    return "\n".join(parts)


def render_grid(grid_size: int, padding: int, step: float) -> str:
    """Render faint Kamea grid."""
    parts = []

    for index in range(grid_size):
        position = padding + (index * step)

        parts.append(
            (
                f'<line x1="{padding}" y1="{position:.2f}" '
                f'x2="{padding + step * (grid_size - 1):.2f}" y2="{position:.2f}" '
                f'stroke="#334155" stroke-width="1" stroke-opacity="0.35" />'
            )
        )

        parts.append(
            (
                f'<line x1="{position:.2f}" y1="{padding}" '
                f'x2="{position:.2f}" y2="{padding + step * (grid_size - 1):.2f}" '
                f'stroke="#334155" stroke-width="1" stroke-opacity="0.35" />'
            )
        )

    return "\n".join(parts)


def render_legend(layers: list[dict[str, Any]], width: int, height: int) -> str:
    """Render legend."""
    parts = []
    x = 80
    y = height - 60

    for index, layer in enumerate(layers):
        cipher = layer["cipher"]
        style = CIPHER_STYLES.get(
            cipher,
            {
                "stroke": "#ffffff",
                "label": cipher,
            },
        )

        item_x = x + (index * 240)

        parts.append(
            (
                f'<circle cx="{item_x}" cy="{y}" r="8" '
                f'fill="{style["stroke"]}" fill-opacity="0.8" />'
            )
        )
        parts.append(
            (
                f'<text x="{item_x + 18}" y="{y + 6}" '
                f'font-size="18" fill="#f8fafc">{style["label"]}</text>'
            )
        )

    return "\n".join(parts)


def coordinate_to_svg_point(
    coordinate: list[int] | tuple[int, int],
    padding: int,
    step: float,
) -> tuple[float, float]:
    """Convert row/column coordinate to SVG x/y point."""
    row, col = coordinate
    x = padding + (col * step)
    y = padding + (row * step)

    return x, y


def node_from_coordinate(layer: dict[str, Any], coordinate: list[int] | tuple[int, int]) -> int:
    """Resolve wrapped node value from coordinate using visual path."""
    path_views = layer["features"]["path_views"]
    coordinates = path_views["render_path"]["coordinates"]
    values = path_views["render_path"]["wrapped_values"]

    for value, candidate in zip(values, coordinates):
        if list(candidate) == list(coordinate):
            return value

    return -1


def svg_header(width: int, height: int) -> str:
    """SVG header."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )


def background_rect(width: int, height: int) -> str:
    """Background rectangle."""
    return (
        f'<rect width="{width}" height="{height}" '
        f'fill="#020617" />'
    )


def title_text(planet: str, width: int) -> str:
    """Title text."""
    return (
        f'<text x="{width / 2:.2f}" y="42" '
        f'font-size="28" '
        f'font-weight="700" '
        f'fill="#f8fafc" '
        f'text-anchor="middle">{planet} Composite</text>'
    )