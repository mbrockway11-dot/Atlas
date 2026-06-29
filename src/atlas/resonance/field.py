"""Composite resonance field for Atlas.

This module converts the Composite Overlay into an individual resonance field.
It separates one person's symbolic topology into:

- core
- adaptive
- peripheral

The field is built from cross-cipher, cross-planet, and cross-layer recurrence.
"""

from __future__ import annotations

from typing import Any


CORE_THRESHOLD = 0.80
ADAPTIVE_THRESHOLD = 0.45


def build_resonance_field(
    composite_overlay: dict[str, Any],
) -> dict[str, Any]:
    """Build resonance field from a composite overlay."""
    nodes = [
        enrich_resonance_record(record)
        for record in composite_overlay["nodes"]
    ]

    edges = [
        enrich_resonance_record(record)
        for record in composite_overlay["edges"]
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "core": {
            "nodes": [node for node in nodes if node["field_region"] == "core"],
            "edges": [edge for edge in edges if edge["field_region"] == "core"],
        },
        "adaptive": {
            "nodes": [node for node in nodes if node["field_region"] == "adaptive"],
            "edges": [edge for edge in edges if edge["field_region"] == "adaptive"],
        },
        "peripheral": {
            "nodes": [node for node in nodes if node["field_region"] == "peripheral"],
            "edges": [edge for edge in edges if edge["field_region"] == "peripheral"],
        },
        "summary": build_resonance_summary(nodes, edges),
    }


def enrich_resonance_record(record: dict[str, Any]) -> dict[str, Any]:
    """Add normalized resonance metrics to one composite overlay record."""
    cipher_ratio = record["cipher_count"] / 3
    planet_ratio = record["planet_count"] / 7
    layer_ratio = record["layer_count"] / 21

    total_weight = float(record["total_weight"])
    weight_factor = min(total_weight / 50.0, 1.0)

    resonance_index = (
        cipher_ratio * 0.35
        + planet_ratio * 0.25
        + layer_ratio * 0.25
        + weight_factor * 0.15
    )

    enriched = dict(record)
    enriched["cipher_ratio"] = cipher_ratio
    enriched["planet_ratio"] = planet_ratio
    enriched["layer_ratio"] = layer_ratio
    enriched["weight_factor"] = weight_factor
    enriched["resonance_index"] = resonance_index
    enriched["field_region"] = classify_field_region(resonance_index)

    return enriched


def classify_field_region(resonance_index: float) -> str:
    """Classify a resonance index into a field region."""
    if resonance_index >= CORE_THRESHOLD:
        return "core"

    if resonance_index >= ADAPTIVE_THRESHOLD:
        return "adaptive"

    return "peripheral"


def build_resonance_summary(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize resonance field."""
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "core_node_count": count_region(nodes, "core"),
        "core_edge_count": count_region(edges, "core"),
        "adaptive_node_count": count_region(nodes, "adaptive"),
        "adaptive_edge_count": count_region(edges, "adaptive"),
        "peripheral_node_count": count_region(nodes, "peripheral"),
        "peripheral_edge_count": count_region(edges, "peripheral"),
        "top_resonant_nodes": top_resonant(nodes),
        "top_resonant_edges": top_resonant(edges),
    }


def count_region(records: list[dict[str, Any]], region: str) -> int:
    """Count records in a field region."""
    return len(
        [
            record
            for record in records
            if record["field_region"] == region
        ]
    )


def top_resonant(
    records: list[dict[str, Any]],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return top records by resonance index."""
    return sorted(
        records,
        key=lambda record: record["resonance_index"],
        reverse=True,
    )[:limit]