"""Atlas v2 canonical Identity Graph.

This graph represents ONE identity topology.

The 21 Kamea/cipher outputs are treated as construction passes.
They do not remain as separate final graphs. Their layer identity is
preserved only as construction history / provenance.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def build_identity_graph_v2(acf: dict[str, Any]) -> dict[str, Any]:
    """Build one canonical Identity Graph from 21 construction passes."""
    graph = empty_identity_graph(acf["identity"]["name"])

    for layer in acf["identity_graph"]["layers"]:
        apply_construction_pass(graph, layer)

    finalize_identity_graph(graph)

    return graph


def empty_identity_graph(name: str) -> dict[str, Any]:
    """Create an empty Identity Graph."""
    return {
        "name": name,
        "version": "2.0",
        "nodes": {},
        "edges": {},
        "construction_passes": [],
        "summary": {},
    }


def apply_construction_pass(
    graph: dict[str, Any],
    layer: dict[str, Any],
) -> None:
    """Apply one Kamea/cipher construction pass into the single graph."""
    layer_id = layer["layer_id"]
    cipher = layer["cipher"]
    planet = layer["planet"]

    path = layer["features"]["path_views"]["analysis_path"]
    visits = path["visit_history"]["visits"]

    graph["construction_passes"].append(
        {
            "layer_id": layer_id,
            "cipher": cipher,
            "planet": planet,
            "visit_count": len(visits),
        }
    )

    for visit in visits:
        apply_node_visit(
            graph=graph,
            visit=visit,
            layer_id=layer_id,
            cipher=cipher,
            planet=planet,
        )

    for source, target in zip(visits[:-1], visits[1:]):
        apply_edge_visit(
            graph=graph,
            source=source,
            target=target,
            layer_id=layer_id,
            cipher=cipher,
            planet=planet,
        )


def apply_node_visit(
    graph: dict[str, Any],
    visit: dict[str, Any],
    layer_id: str,
    cipher: str,
    planet: str,
) -> None:
    """Apply one node visit to the Identity Graph."""
    node_id = str(visit["node"])

    if node_id not in graph["nodes"]:
        graph["nodes"][node_id] = {
            "id": node_id,
            "kind": "node",
            "weight": 0,
            "visit_count": 0,
            "max_depth": 0,
            "coordinates": [],
            "ciphers": set(),
            "planets": set(),
            "construction_history": [],
        }

    node = graph["nodes"][node_id]

    node["weight"] += 1
    node["visit_count"] += 1
    node["max_depth"] = max(node["max_depth"], visit["visit_depth"])
    node["coordinates"].append(visit["coordinate"])
    node["ciphers"].add(cipher)
    node["planets"].add(planet)
    node["construction_history"].append(
        {
            "layer_id": layer_id,
            "cipher": cipher,
            "planet": planet,
            "sequence_index": visit["sequence_index"],
            "visit_depth": visit["visit_depth"],
            "coordinate": visit["coordinate"],
        }
    )


def apply_edge_visit(
    graph: dict[str, Any],
    source: dict[str, Any],
    target: dict[str, Any],
    layer_id: str,
    cipher: str,
    planet: str,
) -> None:
    """Apply one directed edge traversal to the Identity Graph."""
    source_id = str(source["node"])
    target_id = str(target["node"])
    edge_id = f"{source_id}->{target_id}"

    if edge_id not in graph["edges"]:
        graph["edges"][edge_id] = {
            "id": edge_id,
            "kind": "edge",
            "source": source_id,
            "target": target_id,
            "weight": 0,
            "traversal_count": 0,
            "ciphers": set(),
            "planets": set(),
            "construction_history": [],
        }

    edge = graph["edges"][edge_id]

    edge["weight"] += 1
    edge["traversal_count"] += 1
    edge["ciphers"].add(cipher)
    edge["planets"].add(planet)
    edge["construction_history"].append(
        {
            "layer_id": layer_id,
            "cipher": cipher,
            "planet": planet,
            "source_sequence_index": source["sequence_index"],
            "target_sequence_index": target["sequence_index"],
        }
    )


def finalize_identity_graph(graph: dict[str, Any]) -> None:
    """Finalize graph by converting sets and adding summary metrics."""
    for node in graph["nodes"].values():
        node["ciphers"] = sorted(node["ciphers"])
        node["planets"] = sorted(node["planets"])
        node["cipher_count"] = len(node["ciphers"])
        node["planet_count"] = len(node["planets"])
        node["construction_count"] = len(node["construction_history"])
        node["coordinate_consensus"] = most_common_coordinate(node["coordinates"])

    for edge in graph["edges"].values():
        edge["ciphers"] = sorted(edge["ciphers"])
        edge["planets"] = sorted(edge["planets"])
        edge["cipher_count"] = len(edge["ciphers"])
        edge["planet_count"] = len(edge["planets"])
        edge["construction_count"] = len(edge["construction_history"])

    graph["summary"] = build_identity_graph_summary(graph)


def most_common_coordinate(coordinates: list[list[int] | tuple[int, int]]) -> list[int] | None:
    """Return most common coordinate for a merged node."""
    if not coordinates:
        return None

    counts: dict[tuple[int, int], int] = defaultdict(int)

    for coordinate in coordinates:
        counts[tuple(coordinate)] += 1

    coordinate, _ = max(
        counts.items(),
        key=lambda item: item[1],
    )

    return list(coordinate)


def build_identity_graph_summary(graph: dict[str, Any]) -> dict[str, Any]:
    """Build summary for one canonical Identity Graph."""
    nodes = list(graph["nodes"].values())
    edges = list(graph["edges"].values())

    core_candidates = [
        node
        for node in nodes
        if node["cipher_count"] == 3
        and node["planet_count"] >= 2
    ]

    return {
        "construction_pass_count": len(graph["construction_passes"]),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "core_candidate_count": len(core_candidates),
        "max_node_weight": max([node["weight"] for node in nodes], default=0),
        "max_edge_weight": max([edge["weight"] for edge in edges], default=0),
        "top_nodes": top_records(nodes),
        "top_edges": top_records(edges),
    }


def top_records(
    records: list[dict[str, Any]],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return top weighted graph records."""
    return sorted(
        records,
        key=lambda record: (
            record["weight"],
            record["cipher_count"],
            record["planet_count"],
        ),
        reverse=True,
    )[:limit]