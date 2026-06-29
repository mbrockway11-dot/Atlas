"""Essence 3D SVG export."""

from pathlib import Path

from atlas.export.svg import export_graph_svg_3d
from atlas.topology.graph import TopologyGraph


def export_essence_svg_3d(
    graph: TopologyGraph,
    output_path: str | Path,
) -> Path:
    """Export essence graph as pseudo-3D SVG.

    Uses a 9x9 canvas because the Moon Kamea is the largest current grid.
    """
    return export_graph_svg_3d(
        graph=graph,
        output_path=output_path,
        grid_size=9,
        canvas_size=900,
        padding=90,
        depth_offset=5.0,
    )