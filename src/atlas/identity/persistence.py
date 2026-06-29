"""Identity persistence engine.

Consensus is measured by persistence across independent identity layers,
not by averaging metrics.
"""

from collections import Counter, defaultdict
from typing import Any


DEFAULT_PERSISTENCE_THRESHOLD = 0.50


def build_identity_persistence(
    identity_graph: dict[str, Any],
    threshold: float = DEFAULT_PERSISTENCE_THRESHOLD,
) -> dict[str, Any]:
    """Build persistent and residual structures from an Identity Topology Graph."""
    layers = identity_graph["layers"]
    layer_count = len(layers)

    node_records = collect_node_records(layers)
    edge_records = collect_edge_records(layers)

    persistent_nodes, residual_nodes = split_by_persistence(
        node_records,
        layer_count,
        threshold,
    )
    persistent_edges, residual_edges = split_by_persistence(
        edge_records,
        layer_count,
        threshold,
    )

    return {
        "name": identity_graph["name"],
        "layer_count": layer_count,
        "threshold": threshold,
        "persistent_nodes": persistent_nodes,
        "residual_nodes": residual_nodes,
        "persistent_edges": persistent_edges,
        "residual_edges": residual_edges,
        "summary": build_persistence_summary(
            persistent_nodes,
            residual_nodes,
            persistent_edges,
            residual_edges,
            layer_count,
            threshold,
        ),
    }


def collect_node_records(layers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Collect node occurrences across identity layers."""
    records: dict[str, dict[str, Any]] = {}

    for layer in layers:
        layer_id = layer["layer_id"]
        analysis_path = layer["features"]

        visit_history = _get_visit_history(layer)
        node_weights = visit_history["node_weights"]
        node_histories = visit_history["node_histories"]

        for node, weight in node_weights.items():
            node_key = str(node)

            if node_key not in records:
                records[node_key] = {
                    "id": node_key,
                    "kind": "node",
                    "layers_present": [],
                    "occurrence_count": 0,
                    "total_weight": 0,
                    "histories": [],
                }

            records[node_key]["layers_present"].append(layer_id)
            records[node_key]["occurrence_count"] += 1
            records[node_key]["total_weight"] += weight
            records[node_key]["histories"].append(
                {
                    "layer_id": layer_id,
                    "visits": node_histories[node_key],
                }
            )

    return records


def collect_edge_records(layers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Collect edge occurrences across identity layers."""
    records: dict[str, dict[str, Any]] = {}

    for layer in layers:
        layer_id = layer["layer_id"]
        edge_weights = _get_edge_weights(layer)

        for edge_key, weight in edge_weights.items():
            if edge_key not in records:
                records[edge_key] = {
                    "id": edge_key,
                    "kind": "edge",
                    "layers_present": [],
                    "occurrence_count": 0,
                    "total_weight": 0,
                    "histories": [],
                }

            records[edge_key]["layers_present"].append(layer_id)
            records[edge_key]["occurrence_count"] += 1
            records[edge_key]["total_weight"] += weight
            records[edge_key]["histories"].append(
                {
                    "layer_id": layer_id,
                    "weight": weight,
                }
            )

    return records


def split_by_persistence(
    records: dict[str, dict[str, Any]],
    layer_count: int,
    threshold: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split records into persistent and residual lists."""
    persistent = []
    residual = []

    for record in records.values():
        enriched = enrich_persistence_record(record, layer_count)

        if enriched["persistence"] >= threshold:
            persistent.append(enriched)
        else:
            residual.append(enriched)

    persistent = sorted(
        persistent,
        key=lambda item: (item["persistence"], item["total_weight"]),
        reverse=True,
    )
    residual = sorted(
        residual,
        key=lambda item: (item["persistence"], item["total_weight"]),
        reverse=True,
    )

    return persistent, residual


def enrich_persistence_record(
    record: dict[str, Any],
    layer_count: int,
) -> dict[str, Any]:
    """Attach persistence metrics to a node or edge record."""
    persistence = (
        record["occurrence_count"] / layer_count
        if layer_count
        else 0.0
    )

    average_weight = (
        record["total_weight"] / record["occurrence_count"]
        if record["occurrence_count"]
        else 0.0
    )

    enriched = dict(record)
    enriched["persistence"] = persistence
    enriched["average_weight"] = average_weight
    enriched["missing_layers"] = layer_count - record["occurrence_count"]

    if record["kind"] == "node":
        enriched.update(build_node_trajectory_metrics(record))

    return enriched


def build_node_trajectory_metrics(record: dict[str, Any]) -> dict[str, float]:
    """Build trajectory metrics from node visit histories."""
    all_depths = []
    all_intervals = []

    for history in record["histories"]:
        visits = history["visits"]
        sequence_indices = [visit["sequence_index"] for visit in visits]
        depths = [visit["visit_depth"] for visit in visits]

        all_depths.extend(depths)

        if len(sequence_indices) > 1:
            all_intervals.extend(
                [
                    later - earlier
                    for earlier, later in zip(
                        sequence_indices[:-1],
                        sequence_indices[1:],
                    )
                ]
            )

    return {
        "average_depth": _mean(all_depths),
        "max_depth": max(all_depths) if all_depths else 0,
        "average_revisit_interval": _mean(all_intervals),
    }


def build_persistence_summary(
    persistent_nodes: list[dict[str, Any]],
    residual_nodes: list[dict[str, Any]],
    persistent_edges: list[dict[str, Any]],
    residual_edges: list[dict[str, Any]],
    layer_count: int,
    threshold: float,
) -> dict[str, Any]:
    """Build summary for identity persistence."""
    total_nodes = len(persistent_nodes) + len(residual_nodes)
    total_edges = len(persistent_edges) + len(residual_edges)

    return {
        "layer_count": layer_count,
        "threshold": threshold,
        "persistent_node_count": len(persistent_nodes),
        "residual_node_count": len(residual_nodes),
        "persistent_edge_count": len(persistent_edges),
        "residual_edge_count": len(residual_edges),
        "node_persistence_ratio": (
            len(persistent_nodes) / total_nodes
            if total_nodes
            else 0.0
        ),
        "edge_persistence_ratio": (
            len(persistent_edges) / total_edges
            if total_edges
            else 0.0
        ),
        "top_persistent_nodes": persistent_nodes[:10],
        "top_persistent_edges": persistent_edges[:10],
    }


def _get_visit_history(layer: dict[str, Any]) -> dict[str, Any]:
    """Get visit history from identity layer."""
    return layer["features"]["path_views"]["analysis_path"]["visit_history"]


def _get_edge_weights(layer: dict[str, Any]) -> dict[str, int]:
    """Get edge weights from identity layer."""
    return layer["features"]["path_views"]["analysis_path"]["edge_weights"]


def _mean(values: list[float | int]) -> float:
    """Mean helper."""
    if not values:
        return 0.0

    return sum(values) / len(values)