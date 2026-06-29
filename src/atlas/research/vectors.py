"""Atlas canonical vector builder."""

from __future__ import annotations

from typing import Any

PRIMARY_METRICS = [
    "node_coverage",
    "density",
    "entropy",
    "axis_strength",
    "unique_nodes",
    "unique_edges",
    "max_node_weight",
    "max_depth",
    "self_loops",
]


def build_layer_vector(
    row: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert one research row into the canonical Atlas
    feature vector.
    """

    vector = {
        metric: float(row[metric])
        for metric in PRIMARY_METRICS
    }

    return {
        "name": row["name"],
        "cipher": row["cipher"],
        "planet": row["planet"],
        "vector": vector,
    }


def build_profile_vectors(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build one canonical vector per layer.
    """

    return [
        build_layer_vector(row)
        for row in rows
    ]