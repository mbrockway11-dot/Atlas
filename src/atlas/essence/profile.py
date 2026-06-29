"""Essence profile generation."""

from pathlib import Path

from atlas.essence.builder import build_essence_graph
from atlas.essence.export_svg import export_essence_svg_3d
from atlas.export.json import export_graph_with_signature_json
from atlas.profiles.composite import _safe_name
from atlas.signatures.fingerprint import build_topology_signature


def build_essence_profile(name: str, output_dir: str | Path) -> dict[str, Path]:
    """Build and export essence graph, signature JSON, and 3D SVG."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    graph = build_essence_graph(name)
    signature = build_topology_signature(graph)

    safe = _safe_name(name)

    json_path = path / f"{safe}_essence_graph.json"
    svg_path = path / f"{safe}_essence_topology_3d.svg"

    export_graph_with_signature_json(
        graph=graph,
        signature=signature,
        output_path=json_path,
    )

    export_essence_svg_3d(
        graph=graph,
        output_path=svg_path,
    )

    return {
        "json": json_path,
        "svg": svg_path,
    }