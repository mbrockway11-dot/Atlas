
"""Kamea Flow construction."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

from atlas.kamea_flow.extractor import extract_kamea_flow_steps
from atlas.kamea_flow.models import KameaFlowEdge, KameaFlowStep, flow_edge_to_dict, flow_step_to_dict


def build_kamea_flow(payload: dict[str, Any]) -> dict[str, Any]:
    """Build directed Kamea flow from canonical payload."""
    steps = extract_kamea_flow_steps(payload)
    edges = build_flow_edges(steps)

    return {
        "success": True,
        "profile_key": payload.get("profile_key"),
        "step_count": len(steps),
        "edge_count": len(edges),
        "steps": [flow_step_to_dict(item) for item in steps],
        "edges": [flow_edge_to_dict(item) for item in edges],
        "summary": build_flow_summary(steps, edges),
    }


def build_flow_edges(steps: list[KameaFlowStep]) -> list[KameaFlowEdge]:
    """Build directed weighted edges from ordered steps."""
    edge_counter: Counter[tuple[str, str, str, str]] = Counter()
    edge_geometry: dict[tuple[str, str, str, str], tuple[float, float, float]] = {}

    streams: dict[str, list[KameaFlowStep]] = {}
    for step in steps:
        streams.setdefault(step.stream_id, []).append(step)

    for stream_id, stream_steps in streams.items():
        ordered = sorted(stream_steps, key=lambda item: item.stream_index)
        for left, right in zip(ordered, ordered[1:]):
            key = (left.node, right.node, left.cipher, left.planet)
            edge_counter[key] += 1

            dx = right.x - left.x
            dy = right.y - left.y
            distance = math.sqrt(dx * dx + dy * dy)

            edge_geometry[key] = (distance, dx, dy)

    edges = []

    for key, count in edge_counter.items():
        source, target, cipher, planet = key
        distance, dx, dy = edge_geometry[key]

        edges.append(
            KameaFlowEdge(
                source=source,
                target=target,
                cipher=cipher,
                planet=planet,
                stream_id=f"{cipher}::{planet}",
                count=count,
                distance=round(distance, 6),
                direction_x=round(dx, 6),
                direction_y=round(dy, 6),
            )
        )

    edges.sort(key=lambda item: (-item.count, item.cipher, item.planet, item.source, item.target))
    return edges


def build_flow_summary(
    steps: list[KameaFlowStep],
    edges: list[KameaFlowEdge],
) -> dict[str, Any]:
    """Build compact flow summary."""
    node_visits = Counter(step.node for step in steps)
    cipher_counts = Counter(step.cipher for step in steps)
    planet_counts = Counter(step.planet for step in steps)

    repeated_nodes = [
        {"node": node, "visits": count}
        for node, count in node_visits.most_common()
        if count > 1
    ]

    return {
        "unique_node_count": len(node_visits),
        "repeated_node_count": len(repeated_nodes),
        "max_node_visits": max(node_visits.values()) if node_visits else 0,
        "cipher_counts": dict(sorted(cipher_counts.items())),
        "planet_counts": dict(sorted(planet_counts.items())),
        "top_repeated_nodes": repeated_nodes[:20],
        "total_path_distance": round(sum(edge.distance * edge.count for edge in edges), 6),
        "mean_edge_distance": round(
            sum(edge.distance for edge in edges) / len(edges),
            6,
        ) if edges else 0.0,
    }
