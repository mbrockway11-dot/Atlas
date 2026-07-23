"""SVG rendering for invariant Kamea riverbeds."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


PLANET_COLORS = {
    "saturn": "#94a3b8",
    "jupiter": "#60a5fa",
    "mars": "#f87171",
    "sun": "#fbbf24",
    "venus": "#f472b6",
    "mercury": "#34d399",
    "moon": "#c4b5fd",
}


def render_planetary_riverbed_svg(riverbed: dict[str, Any], *, output_size: int = 800) -> str:
    planet = str(riverbed.get("planet") or "unknown")
    nodes = riverbed.get("invariant_nodes", []) or []
    edges = riverbed.get("invariant_edges", []) or []
    node_map = {str(node.get("node")): node for node in nodes}
    grid_size = _grid_size(nodes)
    padding = 90
    usable = output_size - padding * 2
    step = usable / max(grid_size - 1, 1)
    color = PLANET_COLORS.get(planet, "#e2e8f0")
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{output_size}" height="{output_size}" viewBox="0 0 {output_size} {output_size}">',
        f'<rect width="{output_size}" height="{output_size}" fill="#020617"/>',
        f'<text x="{output_size / 2}" y="42" fill="#f8fafc" font-size="28" font-weight="700" text-anchor="middle">{escape(planet.title())} Invariant Riverbed</text>',
        f'<text x="{output_size / 2}" y="70" fill="#94a3b8" font-size="15" text-anchor="middle">shared by at least two cipher tributaries</text>',
    ]
    for index in range(grid_size):
        point = padding + index * step
        extent = padding + (grid_size - 1) * step
        parts.append(f'<line x1="{padding}" y1="{point:.2f}" x2="{extent:.2f}" y2="{point:.2f}" stroke="#334155" stroke-opacity="0.35"/>')
        parts.append(f'<line x1="{point:.2f}" y1="{padding}" x2="{point:.2f}" y2="{extent:.2f}" stroke="#334155" stroke-opacity="0.35"/>')
    for edge in edges:
        source = node_map.get(str(edge.get("source")))
        target = node_map.get(str(edge.get("target")))
        if not source or not target:
            continue
        x1, y1 = _point(source, padding, step)
        x2, y2 = _point(target, padding, step)
        coverage = int(edge.get("cipher_coverage") or 1)
        parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{1.5 + coverage:.2f}" stroke-opacity="0.72" stroke-linecap="round"/>')
    for node in nodes:
        x, y = _point(node, padding, step)
        coverage = int(node.get("cipher_coverage") or 1)
        radius = 6 + coverage * 2
        label = escape(str(node.get("local_node") or node.get("value") or ""))
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius}" fill="{color}" fill-opacity="0.55" stroke="{color}" stroke-width="2"/>')
        parts.append(f'<text x="{x:.2f}" y="{y - radius - 5:.2f}" fill="#f8fafc" font-size="13" text-anchor="middle">{label}</text>')
    parts.append(f'<text x="{output_size / 2}" y="{output_size - 24}" fill="#94a3b8" font-size="14" text-anchor="middle">nodes {riverbed.get("invariant_node_count", 0)} · channels {riverbed.get("invariant_edge_count", 0)} · node consensus {riverbed.get("node_consensus_ratio", 0)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def export_planetary_riverbed_svg(riverbed: dict[str, Any], output_path: str | Path, *, output_size: int = 800) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_planetary_riverbed_svg(riverbed, output_size=output_size), encoding="utf-8")
    return path


def _grid_size(nodes: list[dict[str, Any]]) -> int:
    return max([int(node.get("grid_size") or 0) for node in nodes] + [0]) or _infer_grid_size(nodes)


def _infer_grid_size(nodes: list[dict[str, Any]]) -> int:
    maximum = 0
    for node in nodes:
        coordinate = node.get("coordinate", [0, 0])
        maximum = max(maximum, int(float(coordinate[0])), int(float(coordinate[1])))
    return maximum + 1 if nodes else 3


def _point(node: dict[str, Any], padding: int, step: float) -> tuple[float, float]:
    coordinate = node.get("coordinate", [0, 0])
    x, y = float(coordinate[0]), float(coordinate[1])
    return padding + x * step, padding + y * step
