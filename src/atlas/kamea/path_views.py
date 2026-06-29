"""Analysis and render path views for Kamea paths."""

from collections import Counter
from typing import Any

from atlas.kamea.visit_history import build_node_visit_history


def build_kamea_path_views(kamea_path: Any) -> dict:
    """Build full analysis path and deduplicated render path.

    Analysis path preserves all repeated values.
    Render path removes repeated wrapped values while preserving first occurrence order.
    Visit history preserves repeated nodes as z-axis depth.
    """
    raw_values = list(kamea_path.raw_values)
    wrapped_values = list(kamea_path.reduced_values)
    coordinates = [tuple(coord) for coord in kamea_path.coordinates]

    render_values = []
    render_coordinates = []
    seen = set()

    for value, coordinate in zip(wrapped_values, coordinates):
        if value in seen:
            continue

        seen.add(value)
        render_values.append(value)
        render_coordinates.append(coordinate)

    return {
        "analysis_path": {
            "raw_values": raw_values,
            "wrapped_values": wrapped_values,
            "coordinates": [list(coord) for coord in coordinates],
            "node_weights": dict(Counter(wrapped_values)),
            "edge_weights": _edge_weights(wrapped_values),
            "coordinate_edge_weights": _coordinate_edge_weights(coordinates),
            "visit_history": build_node_visit_history(kamea_path),
        },
        "render_path": {
            "wrapped_values": render_values,
            "coordinates": [list(coord) for coord in render_coordinates],
        },
    }


def _edge_weights(values: list[int]) -> dict[str, int]:
    """Build weighted edges from wrapped values."""
    edges = Counter(zip(values[:-1], values[1:]))

    return {
        f"{source}->{target}": weight
        for (source, target), weight in edges.items()
    }


def _coordinate_edge_weights(coordinates: list[tuple[int, int]]) -> list[dict]:
    """Build weighted coordinate edges."""
    edges = Counter(zip(coordinates[:-1], coordinates[1:]))

    return [
        {
            "source": list(source),
            "target": list(target),
            "weight": weight,
        }
        for (source, target), weight in edges.items()
    ]