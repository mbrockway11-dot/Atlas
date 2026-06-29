"""Visualization render options."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RenderOptions:
    """Options for Atlas SVG renderers."""

    mode: str = "overlay"
    show_node_labels: bool = True
    show_visit_depth: bool = True
    show_edge_weights: bool = True
    color_by_cipher: bool = True
    show_grid: bool = True
    output_size: int = 1000
    padding: int = 80