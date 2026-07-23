"""Invariant riverbed extraction across Kamea cipher tributaries."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


RIVERBED_VERSION = "1.0.0"


def build_invariant_riverbed(flow: dict[str, Any], *, minimum_cipher_coverage: int = 2) -> dict[str, Any]:
    """Find same-planet nodes and directed channels shared across ciphers.

    A riverbed is an invariant of repeated encodings, not a claim about literal
    consciousness. Planets remain separate coordinate fields; raw values from
    different Kameas are never treated as the same node.
    """
    steps = flow.get("steps", []) or []
    edges = flow.get("edges", []) or []
    planets = sorted({str(step.get("planet")) for step in steps})
    rows = [
        _planetary_riverbed(planet, steps, edges, minimum_cipher_coverage)
        for planet in planets
    ]
    return {
        "success": True,
        "version": RIVERBED_VERSION,
        "definition": "Same-planet nodes and directed channels reproduced by at least two independent cipher streams.",
        "claim_type": "deterministic_symbolic_structure",
        "causal_claim": False,
        "minimum_cipher_coverage": minimum_cipher_coverage,
        "planetary_riverbeds": rows,
        "summary": {
            "planet_count": len(rows),
            "invariant_node_count": sum(row["invariant_node_count"] for row in rows),
            "invariant_edge_count": sum(row["invariant_edge_count"] for row in rows),
            "mean_node_consensus": _mean(row["node_consensus_ratio"] for row in rows),
            "mean_edge_consensus": _mean(row["edge_consensus_ratio"] for row in rows),
            "strongest_node_consensus_planet": _strongest(rows, "node_consensus_ratio"),
            "strongest_edge_consensus_planet": _strongest(rows, "edge_consensus_ratio"),
        },
    }


def _planetary_riverbed(planet: str, steps: list[dict[str, Any]], edges: list[dict[str, Any]], minimum: int) -> dict[str, Any]:
    planet_steps = [row for row in steps if str(row.get("planet")) == planet]
    planet_edges = [row for row in edges if str(row.get("planet")) == planet]
    node_streams: dict[str, set[str]] = defaultdict(set)
    node_geometry: dict[str, dict[str, Any]] = {}
    for step in planet_steps:
        node = str(step.get("node"))
        node_streams[node].add(str(step.get("stream_id")))
        node_geometry[node] = {
            "node": node,
            "local_node": step.get("local_node"),
            "value": step.get("value"),
            "coordinate": [step.get("x"), step.get("y")],
            "normalized_coordinate": [step.get("normalized_x"), step.get("normalized_y")],
            "grid_size": step.get("grid_size"),
        }
    edge_streams: dict[tuple[str, str], set[str]] = defaultdict(set)
    edge_counts: Counter[tuple[str, str]] = Counter()
    for edge in planet_edges:
        key = (str(edge.get("source")), str(edge.get("target")))
        edge_streams[key].add(str(edge.get("stream_id")))
        edge_counts[key] += int(edge.get("count") or 1)
    invariant_nodes = []
    for node, streams in node_streams.items():
        if len(streams) >= minimum:
            invariant_nodes.append({**node_geometry[node], "cipher_coverage": len(streams), "streams": sorted(streams)})
    invariant_edges = [
        {"source": source, "target": target, "cipher_coverage": len(streams), "streams": sorted(streams), "total_traversals": edge_counts[(source, target)]}
        for (source, target), streams in edge_streams.items()
        if len(streams) >= minimum
    ]
    invariant_nodes.sort(key=lambda row: (-row["cipher_coverage"], float(row.get("value") or 0)))
    invariant_edges.sort(key=lambda row: (-row["cipher_coverage"], -row["total_traversals"], row["source"], row["target"]))
    return {
        "planet": planet,
        "stream_count": len({str(row.get("stream_id")) for row in planet_steps}),
        "union_node_count": len(node_streams),
        "union_edge_count": len(edge_streams),
        "invariant_node_count": len(invariant_nodes),
        "invariant_edge_count": len(invariant_edges),
        "node_consensus_ratio": round(len(invariant_nodes) / len(node_streams), 6) if node_streams else 0.0,
        "edge_consensus_ratio": round(len(invariant_edges) / len(edge_streams), 6) if edge_streams else 0.0,
        "invariant_nodes": invariant_nodes,
        "invariant_edges": invariant_edges,
    }


def _mean(values: Any) -> float:
    items = [float(value) for value in values]
    return round(sum(items) / len(items), 6) if items else 0.0


def _strongest(rows: list[dict[str, Any]], metric: str) -> str | None:
    return max(rows, key=lambda row: (float(row.get(metric) or 0.0), row.get("planet", "")))["planet"] if rows else None
