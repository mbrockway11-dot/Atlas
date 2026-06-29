"""Composite overlay graph for Atlas.

The composite overlay treats all 21 cipher/planet layers as one multiplex field.
It preserves layer identity while measuring cross-layer recurrence.

This module intentionally prepares display-safe fields so Atlas Studio does not
render nested objects as [object Object].
"""

from __future__ import annotations

from typing import Any


def build_composite_overlay(acf: dict[str, Any]) -> dict[str, Any]:
    """Build a multiplex composite overlay from an ACF profile."""
    layers = acf["identity_graph"]["layers"]

    node_index = build_composite_nodes(layers)
    edge_index = build_composite_edges(layers)

    return {
        "name": acf["identity"]["name"],
        "layer_count": len(layers),
        "nodes": list(node_index.values()),
        "edges": list(edge_index.values()),
        "summary": build_overlay_summary(node_index, edge_index, len(layers)),
    }


def build_composite_nodes(layers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build composite node records across all layers."""
    index: dict[str, dict[str, Any]] = {}

    for layer in layers:
        layer_id = layer["layer_id"]
        cipher = layer["cipher"]
        planet = layer["planet"]
        path = layer["features"]["path_views"]["analysis_path"]

        for node, weight in path["node_weights"].items():
            node_key = str(node)

            if node_key not in index:
                index[node_key] = {
                    "id": node_key,
                    "kind": "node",
                    "total_weight": 0.0,
                    "layer_occurrences": [],
                    "ciphers": set(),
                    "planets": set(),
                }

            record = index[node_key]
            numeric_weight = float(weight)

            record["total_weight"] += numeric_weight
            record["layer_occurrences"].append(
                {
                    "layer_id": layer_id,
                    "cipher": cipher,
                    "planet": planet,
                    "weight": numeric_weight,
                }
            )
            record["ciphers"].add(cipher)
            record["planets"].add(planet)

    return normalize_composite_records(index)


def build_composite_edges(layers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build composite edge records across all layers."""
    index: dict[str, dict[str, Any]] = {}

    for layer in layers:
        layer_id = layer["layer_id"]
        cipher = layer["cipher"]
        planet = layer["planet"]
        path = layer["features"]["path_views"]["analysis_path"]

        for edge, weight in path["edge_weights"].items():
            edge_key = normalize_edge_id(edge)

            if edge_key not in index:
                index[edge_key] = {
                    "id": edge_key,
                    "kind": "edge",
                    "total_weight": 0.0,
                    "layer_occurrences": [],
                    "ciphers": set(),
                    "planets": set(),
                }

            record = index[edge_key]
            numeric_weight = float(weight)

            record["total_weight"] += numeric_weight
            record["layer_occurrences"].append(
                {
                    "layer_id": layer_id,
                    "cipher": cipher,
                    "planet": planet,
                    "weight": numeric_weight,
                }
            )
            record["ciphers"].add(cipher)
            record["planets"].add(planet)

    return normalize_composite_records(index)


def normalize_composite_records(
    index: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Convert sets to sorted lists and add resonance/display fields."""
    for record in index.values():
        layer_count = len(record["layer_occurrences"])
        cipher_count = len(record["ciphers"])
        planet_count = len(record["planets"])

        ciphers = sorted(record["ciphers"])
        planets = sorted(record["planets"])

        record["ciphers"] = ciphers
        record["planets"] = planets
        record["layer_count"] = layer_count
        record["cipher_count"] = cipher_count
        record["planet_count"] = planet_count
        record["is_triple_cipher"] = cipher_count == 3
        record["is_multi_planet"] = planet_count > 1

        record["ciphers_text"] = ", ".join(ciphers)
        record["planets_text"] = ", ".join(planets)
        record["layer_occurrences_text"] = format_layer_occurrences(
            record["layer_occurrences"]
        )

        record["resonance_score"] = calculate_resonance_score(
            layer_count=layer_count,
            cipher_count=cipher_count,
            planet_count=planet_count,
            total_weight=record["total_weight"],
        )

    return index


def calculate_resonance_score(
    layer_count: int,
    cipher_count: int,
    planet_count: int,
    total_weight: float,
) -> float:
    """Calculate composite recurrence score.

    This avoids letting raw total_weight dominate the overlay.
    Cross-cipher and cross-planet recurrence matter more than raw Kamea weight.
    """
    recurrence_score = layer_count / 21.0
    cipher_score = cipher_count / 3.0
    planet_score = planet_count / 7.0
    weight_score = total_weight / (total_weight + 25.0) if total_weight > 0 else 0.0

    return (
        recurrence_score * 0.35
        + cipher_score * 0.30
        + planet_score * 0.25
        + weight_score * 0.10
    )


def build_overlay_summary(
    node_index: dict[str, dict[str, Any]],
    edge_index: dict[str, dict[str, Any]],
    total_layers: int,
) -> dict[str, Any]:
    """Build composite overlay summary."""
    nodes = list(node_index.values())
    edges = list(edge_index.values())

    triple_nodes = [
        node
        for node in nodes
        if node["is_triple_cipher"]
    ]
    triple_edges = [
        edge
        for edge in edges
        if edge["is_triple_cipher"]
    ]

    multi_planet_nodes = [
        node
        for node in nodes
        if node["is_multi_planet"]
    ]
    multi_planet_edges = [
        edge
        for edge in edges
        if edge["is_multi_planet"]
    ]

    return {
        "total_layers": total_layers,
        "composite_node_count": len(nodes),
        "composite_edge_count": len(edges),
        "triple_cipher_node_count": len(triple_nodes),
        "triple_cipher_edge_count": len(triple_edges),
        "multi_planet_node_count": len(multi_planet_nodes),
        "multi_planet_edge_count": len(multi_planet_edges),
        "top_resonant_nodes": top_by_resonance(nodes),
        "top_resonant_edges": top_by_resonance(edges),
    }


def top_by_resonance(
    records: list[dict[str, Any]],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return top resonant records."""
    return sorted(
        records,
        key=lambda item: item["resonance_score"],
        reverse=True,
    )[:limit]


def format_layer_occurrences(occurrences: list[dict[str, Any]]) -> str:
    """Format nested layer occurrence records for dashboard display."""
    return "; ".join(
        (
            f"{item['planet']} / {item['cipher']} "
            f"w={float(item['weight']):.2f}"
        )
        for item in occurrences
    )


def normalize_edge_id(edge: Any) -> str:
    """Normalize edge id for stable display."""
    if isinstance(edge, tuple) and len(edge) == 2:
        return f"{edge[0]}->{edge[1]}"

    if isinstance(edge, list) and len(edge) == 2:
        return f"{edge[0]}->{edge[1]}"

    return str(edge)