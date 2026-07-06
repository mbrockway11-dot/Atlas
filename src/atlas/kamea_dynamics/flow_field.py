
"""Kamea flow-field aggregation."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


def build_flow_field(streams: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate all streams into a shared flow field."""
    node_streams: dict[str, set[str]] = defaultdict(set)
    node_visits = Counter()
    edge_visits = Counter()

    for stream in streams:
        stream_id = stream.get("stream_id", "")
        trajectory = stream.get("trajectory", []) or []

        for row in trajectory:
            node = str(row.get("node"))
            node_visits[node] += 1
            node_streams[node].add(stream_id)

        for left, right in zip(trajectory, trajectory[1:]):
            edge_visits[f"{left.get('node')}->{right.get('node')}"] += 1

    return {
        "node_count": len(node_visits),
        "edge_count": len(edge_visits),
        "field_attractors": [
            {
                "node": node,
                "visits": visits,
                "stream_count": len(node_streams[node]),
                "streams": sorted(node_streams[node]),
            }
            for node, visits in node_visits.most_common()
        ],
        "edge_currents": [
            {
                "edge": edge,
                "visits": visits,
            }
            for edge, visits in edge_visits.most_common()
        ],
    }
