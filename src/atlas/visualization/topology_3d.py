"""3D topology scene builder for Atlas."""

from __future__ import annotations

from typing import Any


CIPHER_COLORS = {
    "ordinal": "#3b82f6",
    "hebrew_literal": "#d4af37",
    "hebrew_phonetic": "#a855f7",
}


def build_3d_topology_points(
    acf: dict[str, Any],
    z_mode: str = "visit_depth",
) -> list[dict[str, Any]]:
    """Build 3D node points from all 21 identity layers."""
    points = []

    for layer in acf["identity_graph"]["layers"]:
        layer_id = layer["layer_id"]
        cipher = layer["cipher"]
        planet = layer["planet"]
        grid_size = layer["grid_size"]

        path_views = layer["features"]["path_views"]
        visit_history = path_views["analysis_path"]["visit_history"]

        for visit in visit_history["visits"]:
            row, col = visit["coordinate"]

            points.append(
                {
                    "name": acf["identity"]["name"],
                    "layer_id": layer_id,
                    "cipher": cipher,
                    "planet": planet,
                    "node": visit["node"],
                    "x": col,
                    "y": row,
                    "z": resolve_z_value(visit, grid_size, z_mode),
                    "sequence_index": visit["sequence_index"],
                    "visit_depth": visit["visit_depth"],
                    "color": CIPHER_COLORS.get(cipher, "#ffffff"),
                }
            )

    return points


def build_3d_topology_edges(
    acf: dict[str, Any],
    z_mode: str = "visit_depth",
) -> list[dict[str, Any]]:
    """Build 3D edge segments from visit histories."""
    edges = []

    for layer in acf["identity_graph"]["layers"]:
        layer_id = layer["layer_id"]
        cipher = layer["cipher"]
        planet = layer["planet"]
        grid_size = layer["grid_size"]

        path_views = layer["features"]["path_views"]
        visits = path_views["analysis_path"]["visit_history"]["visits"]

        for source, target in zip(visits[:-1], visits[1:]):
            source_row, source_col = source["coordinate"]
            target_row, target_col = target["coordinate"]

            edges.append(
                {
                    "layer_id": layer_id,
                    "cipher": cipher,
                    "planet": planet,
                    "source_node": source["node"],
                    "target_node": target["node"],
                    "x": [source_col, target_col, None],
                    "y": [source_row, target_row, None],
                    "z": [
                        resolve_z_value(source, grid_size, z_mode),
                        resolve_z_value(target, grid_size, z_mode),
                        None,
                    ],
                    "color": CIPHER_COLORS.get(cipher, "#ffffff"),
                }
            )

    return edges


def resolve_z_value(
    visit: dict[str, Any],
    grid_size: int,
    z_mode: str,
) -> float:
    """Resolve z-axis value."""
    if z_mode == "visit_depth":
        return float(visit["visit_depth"])

    if z_mode == "sequence_order":
        return float(visit["sequence_index"])

    if z_mode == "planet_stack":
        return float(grid_size)

    return float(visit["visit_depth"])