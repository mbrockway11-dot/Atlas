"""Kamea-derived IdentityGraph adapter.

This module bridges the Atlas cipher/Kamea engine into the graph/topology stack.

Pipeline:
identity name
    -> run_all_ciphers()
    -> project_values_to_all_kameas()
    -> build_kamea_path_views()
    -> IdentityGraph v2 shape
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from atlas.ciphers import run_all_ciphers
from atlas.kamea.path_views import build_kamea_path_views
from atlas.kamea.projection import project_values_to_all_kameas


CIPHER_ORDER = [
    "ordinal",
    "hebrew_phonetic",
    "hebrew_literal",
]


def build_kamea_identity_graph(
    profile_payload: dict[str, Any],
    *,
    use_planetary_transform: bool = True,
) -> dict[str, Any]:
    """Build an IdentityGraph v2 from cipher-projected Kamea paths."""
    identity = profile_payload.get("identity", {})
    name = resolve_identity_name(profile_payload)

    cipher_values = run_all_ciphers(name)

    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    construction_passes: list[dict[str, Any]] = []

    for cipher_name in CIPHER_ORDER:
        values = cipher_values.get(cipher_name, [])
        if not values:
            continue

        planetary_paths = project_values_to_all_kameas(
            values,
            use_planetary_transform=use_planetary_transform,
        )

        for planet, kamea_path in planetary_paths.items():
            path_views = build_kamea_path_views(kamea_path)

            construction_passes.append(
                {
                    "cipher": cipher_name,
                    "planet": planet,
                    "value_count": len(values),
                    "path_length": kamea_path.length,
                    "repeated_nodes": dict(kamea_path.repeated_nodes),
                    "repeated_edges": stringify_edge_counts(kamea_path.repeated_edges),
                    "path_views": path_views,
                }
            )

            add_path_to_graph(
                nodes=nodes,
                edges=edges,
                cipher_name=cipher_name,
                planet=planet,
                kamea_path=kamea_path,
                path_views=path_views,
            )

    graph = {
        "name": name,
        "version": "2.0-kamea",
        "source": "atlas.kamea.identity_graph",
        "identity": identity,
        "nodes": nodes,
        "edges": edges,
        "construction_passes": construction_passes,
        "summary": build_summary(nodes, edges, construction_passes),
    }

    return graph


def add_path_to_graph(
    *,
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
    cipher_name: str,
    planet: str,
    kamea_path: Any,
    path_views: dict[str, Any],
) -> None:
    """Merge one cipher/planet Kamea path into graph."""
    wrapped_values = list(kamea_path.reduced_values)
    coordinates = [tuple(coord) for coord in kamea_path.coordinates]

    visit_history = (
        path_views.get("analysis_path", {})
        .get("visit_history", {})
        .get("visits", [])
    )

    previous_node_id = ""

    for index, (wrapped_value, coordinate) in enumerate(zip(wrapped_values, coordinates)):
        visit = visit_history[index] if index < len(visit_history) else {}

        node_id = build_node_id(planet, wrapped_value)

        if node_id not in nodes:
            nodes[node_id] = {
                "id": node_id,
                "label": f"{planet}:{wrapped_value}",
                "type": "kamea_node",
                "value": wrapped_value,
                "coordinate": list(coordinate),
                "weight": 0,
                "cipher_count": 0,
                "planet_count": 0,
                "ciphers": [],
                "planets": [],
                "visits": [],
            }

        node = nodes[node_id]
        node["weight"] += 1

        if cipher_name not in node["ciphers"]:
            node["ciphers"].append(cipher_name)
            node["cipher_count"] = len(node["ciphers"])

        if planet not in node["planets"]:
            node["planets"].append(planet)
            node["planet_count"] = len(node["planets"])

        node["visits"].append(
            {
                "cipher": cipher_name,
                "planet": planet,
                "sequence_index": index,
                "value": wrapped_value,
                "coordinate": list(coordinate),
                "visit_depth": visit.get("visit_depth", 0),
            }
        )

        if previous_node_id:
            edge_id = build_edge_id(previous_node_id, node_id, cipher_name, planet)

            if edge_id not in edges:
                edges[edge_id] = {
                    "id": edge_id,
                    "source": previous_node_id,
                    "target": node_id,
                    "type": "kamea_path",
                    "weight": 0,
                    "cipher": cipher_name,
                    "planet": planet,
                    "visits": [],
                }

            edge = edges[edge_id]
            edge["weight"] += 1
            edge["visits"].append(
                {
                    "cipher": cipher_name,
                    "planet": planet,
                    "sequence_index": index,
                }
            )

        previous_node_id = node_id


def resolve_identity_name(profile_payload: dict[str, Any]) -> str:
    """Resolve canonical identity name."""
    identity = profile_payload.get("identity", {})

    return str(
        identity.get("full_name")
        or identity.get("display_name")
        or identity.get("name")
        or profile_payload.get("name")
        or profile_payload.get("profile_key")
        or "unknown_profile"
    )


def build_node_id(planet: str, value: int) -> str:
    """Build stable node id."""
    return f"kamea:{planet}:{value}"


def build_edge_id(source: str, target: str, cipher_name: str, planet: str) -> str:
    """Build stable edge id."""
    return f"{source}->{target}:{cipher_name}:{planet}"


def stringify_edge_counts(edge_counts: dict[Any, int]) -> dict[str, int]:
    """Convert tuple edge keys into JSON-safe strings."""
    output: dict[str, int] = {}

    for edge, count in edge_counts.items():
        try:
            source, target = edge
            output[f"{source}->{target}"] = count
        except Exception:
            output[str(edge)] = count

    return output


def build_summary(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
    construction_passes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build graph summary."""
    node_values = list(nodes.values())
    edge_values = list(edges.values())

    cipher_counter = Counter()
    planet_counter = Counter()

    for node in node_values:
        for cipher in node.get("ciphers", []):
            cipher_counter[cipher] += 1
        for planet in node.get("planets", []):
            planet_counter[planet] += 1

    return {
        "source": "kamea_identity_graph",
        "node_count": len(node_values),
        "edge_count": len(edge_values),
        "construction_pass_count": len(construction_passes),
        "cipher_count": len(cipher_counter),
        "planet_count": len(planet_counter),
        "repeated_node_count": len(
            [node for node in node_values if node.get("weight", 0) > 1]
        ),
        "multi_cipher_node_count": len(
            [node for node in node_values if node.get("cipher_count", 0) > 1]
        ),
        "multi_planet_node_count": len(
            [node for node in node_values if node.get("planet_count", 0) > 1]
        ),
        "max_node_weight": max(
            [node.get("weight", 0) for node in node_values],
            default=0,
        ),
        "max_edge_weight": max(
            [edge.get("weight", 0) for edge in edge_values],
            default=0,
        ),
        "ciphers": dict(cipher_counter),
        "planets": dict(planet_counter),
    }
