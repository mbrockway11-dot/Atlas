
"""Kamea Flow tributary analysis.

Splits the full Kamea river into ordered tributaries:
3 ciphers ? 7 planets = 21 potential construction streams.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from atlas.kamea_flow.metrics import (
    directional_coherence,
    edge_reuse_ratio,
    flow_entropy,
    path_efficiency,
    recurrence_ratio,
)


TRIBUTARY_VERSION = "1.0.0"


def build_kamea_tributaries(flow: dict[str, Any]) -> dict[str, Any]:
    """Build tributary analysis from a Kamea Flow payload."""
    steps = flow.get("steps", []) or []
    edges = flow.get("edges", []) or []

    grouped_steps = group_steps(steps)
    grouped_edges = group_edges(edges)

    tributaries = []

    for key in sorted(grouped_steps):
        cipher, planet = key
        sub_steps = grouped_steps[key]
        sub_edges = grouped_edges.get(key, [])

        tributaries.append(
            build_tributary_row(
                cipher,
                planet,
                sub_steps,
                sub_edges,
            )
        )

    return {
        "success": True,
        "version": TRIBUTARY_VERSION,
        "tributary_count": len(tributaries),
        "tributaries": tributaries,
        "cross_stream": build_cross_stream_metrics(tributaries),
        "summary": build_summary(tributaries),
    }


def group_steps(steps: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """Group flow steps by cipher/planet."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for step in steps:
        key = (
            str(step.get("cipher") or "unknown_cipher"),
            str(step.get("planet") or "unknown_planet"),
        )
        grouped[key].append(step)

    for key in grouped:
        grouped[key] = sorted(grouped[key], key=lambda item: item.get("stream_index", item.get("index", 0)))

    return dict(grouped)


def group_edges(edges: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """Group flow edges by cipher/planet."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for edge in edges:
        key = (
            str(edge.get("cipher") or "unknown_cipher"),
            str(edge.get("planet") or "unknown_planet"),
        )
        grouped[key].append(edge)

    return dict(grouped)


def build_tributary_row(
    cipher: str,
    planet: str,
    steps: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build one tributary analysis row."""
    node_counts = Counter(str(step.get("node")) for step in steps)
    repeated = [
        {"node": node, "visits": count}
        for node, count in node_counts.most_common()
        if count > 1
    ]

    metrics = {
        "flow_entropy": flow_entropy(steps),
        "recurrence_ratio": recurrence_ratio(steps),
        "directional_coherence": directional_coherence(edges),
        "path_efficiency": path_efficiency(steps, edges),
        "edge_reuse_ratio": edge_reuse_ratio(edges),
    }

    return {
        "stream_id": f"{cipher}::{planet}",
        "cipher": cipher,
        "planet": planet,
        "step_count": len(steps),
        "edge_count": len(edges),
        "unique_node_count": len(node_counts),
        "visited_nodes": sorted(node_counts),
        "repeated_node_count": len(repeated),
        "top_repeated_nodes": repeated[:10],
        "start_node": str(steps[0].get("node")) if steps else "",
        "end_node": str(steps[-1].get("node")) if steps else "",
        "metrics": metrics,
        "signature": classify_tributary(metrics),
    }


def classify_tributary(metrics: dict[str, float]) -> str:
    """Classify tributary behavior."""
    recurrence = float(metrics.get("recurrence_ratio") or 0.0)
    coherence = float(metrics.get("directional_coherence") or 0.0)
    efficiency = float(metrics.get("path_efficiency") or 0.0)
    entropy = float(metrics.get("flow_entropy") or 0.0)

    if recurrence >= 0.35 and coherence < 0.25:
        return "recursive_pool"

    if coherence >= 0.55 and efficiency >= 0.35:
        return "directed_current"

    if entropy >= 0.85 and efficiency < 0.20:
        return "diffuse_field_walk"

    if recurrence >= 0.20:
        return "returning_stream"

    if coherence >= 0.35:
        return "directional_stream"

    return "distributed_stream"


def build_cross_stream_metrics(tributaries: list[dict[str, Any]]) -> dict[str, Any]:
    """Build metrics across tributaries."""
    node_to_streams: dict[str, set[str]] = defaultdict(set)
    start_nodes = Counter()
    end_nodes = Counter()
    signatures = Counter()

    for tributary in tributaries:
        stream_id = tributary.get("stream_id", "")
        signatures[tributary.get("signature", "unknown")] += 1

        if tributary.get("start_node"):
            start_nodes[tributary.get("start_node")] += 1

        if tributary.get("end_node"):
            end_nodes[tributary.get("end_node")] += 1

        for node in tributary.get("visited_nodes", []) or []:
            node_to_streams[str(node)].add(stream_id)

    cross_stream_attractors = [
        {
            "node": node,
            "stream_count": len(streams),
            "streams": sorted(streams),
        }
        for node, streams in node_to_streams.items()
        if len(streams) > 1
    ]

    cross_stream_attractors.sort(
        key=lambda item: (-item["stream_count"], item["node"])
    )

    return {
        "signature_counts": dict(sorted(signatures.items())),
        "shared_start_nodes": top_counts(start_nodes),
        "shared_end_nodes": top_counts(end_nodes),
        "cross_stream_attractors": cross_stream_attractors[:20],
        "cross_stream_attractor_count": len(cross_stream_attractors),
    }


def build_summary(tributaries: list[dict[str, Any]]) -> dict[str, Any]:
    """Build tributary summary."""
    if not tributaries:
        return {
            "tributary_count": 0,
            "mean_entropy": 0.0,
            "mean_recurrence": 0.0,
            "mean_directional_coherence": 0.0,
            "mean_path_efficiency": 0.0,
        }

    return {
        "tributary_count": len(tributaries),
        "mean_entropy": mean_metric(tributaries, "flow_entropy"),
        "mean_recurrence": mean_metric(tributaries, "recurrence_ratio"),
        "mean_directional_coherence": mean_metric(tributaries, "directional_coherence"),
        "mean_path_efficiency": mean_metric(tributaries, "path_efficiency"),
        "strongest_recurrence_streams": top_streams(tributaries, "recurrence_ratio"),
        "strongest_directional_streams": top_streams(tributaries, "directional_coherence"),
        "most_efficient_streams": top_streams(tributaries, "path_efficiency"),
    }


def mean_metric(tributaries: list[dict[str, Any]], metric: str) -> float:
    """Mean metric across tributaries."""
    values = [
        float(item.get("metrics", {}).get(metric) or 0.0)
        for item in tributaries
    ]

    return round(sum(values) / len(values), 6) if values else 0.0


def top_streams(
    tributaries: list[dict[str, Any]],
    metric: str,
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Return top streams by metric."""
    rows = [
        {
            "stream_id": item.get("stream_id"),
            "cipher": item.get("cipher"),
            "planet": item.get("planet"),
            "value": item.get("metrics", {}).get(metric),
            "signature": item.get("signature"),
        }
        for item in tributaries
    ]

    return sorted(
        rows,
        key=lambda item: (-(float(item.get("value") or 0.0)), item.get("stream_id") or ""),
    )[:limit]


def top_counts(counter: Counter, *, limit: int = 10) -> list[dict[str, Any]]:
    """Return top counter rows."""
    return [
        {"node": key, "count": count}
        for key, count in counter.most_common(limit)
        if count > 1
    ]
