"""Graph-of-graphs assembly for the astronomy-first CSS."""

from __future__ import annotations

from typing import Any


STRUCTURAL_MEASUREMENT_VERSION = "1.0.0"


def build_structural_measurement(
    astronomy: dict[str, Any],
    normalized_kamea_graphs: dict[str, Any],
) -> dict[str, Any]:
    """Build the master graph without applying symbolic interpretation."""
    bodies = astronomy.get("bodies", {}) or {}
    aspect_graph = astronomy.get("planet_graph", {}) or {}
    kamea_lookup = {
        key.casefold(): value for key, value in normalized_kamea_graphs.items()
    }
    nodes = []
    for body in sorted(bodies):
        kamea = kamea_lookup.get(body.casefold())
        nodes.append({
            "node_id": body,
            "node_type": "planetary_graph_container",
            "astronomy_ref": f"astronomy.measurements.bodies.{body}",
            "kamea_graph_ref": f"kamea.normalized_graphs.{body.casefold()}"
            if kamea else None,
            "kamea_graph_available": bool(kamea),
            "nested_graph_summary": {
                "node_count": kamea.get("node_count", 0) if kamea else 0,
                "edge_count": kamea.get("edge_count", 0) if kamea else 0,
            },
        })
    edges = [
        {
            "source": row["source"],
            "target": row["target"],
            "relationship": "measured_natal_aspect",
            "aspect_type": row["aspect_type"],
            "angular_separation_degrees": row["angular_separation_degrees"],
            "orb_degrees": row["orb_degrees"],
            "weight": row["orb_strength"],
        }
        for row in aspect_graph.get("edges", [])
        if row.get("aspect_type")
    ]
    feature_vector = flatten_metric_means(normalized_kamea_graphs)
    feature_vector.update({
        "astronomy.body_count": float(len(bodies)),
        "astronomy.aspect_edge_count": float(len(edges)),
    })
    return {
        "success": True,
        "version": STRUCTURAL_MEASUREMENT_VERSION,
        "master_graph": {
            "graph_type": "nested_planetary_graph_of_graphs",
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
            "interpretation_applied": False,
        },
        "feature_vector": feature_vector,
        "topology_classification": {
            "status": "unclassified_pending_population_fit",
            "method": "data-driven clustering required; no manual archetype assigned",
        },
        "similarity": {"status": "pending_population_reference_corpus"},
        "cluster_membership": {"status": "pending_population_fit"},
        "interpretation_applied": False,
    }


def flatten_metric_means(graphs: dict[str, Any]) -> dict[str, float]:
    scalar_keys = sorted({
        key
        for graph in graphs.values()
        for key, value in (graph.get("metrics", {}) or {}).items()
        if isinstance(value, (int, float))
    })
    result = {}
    for key in scalar_keys:
        values = [
            float(graph["metrics"][key])
            for graph in graphs.values()
            if isinstance((graph.get("metrics", {}) or {}).get(key), (int, float))
        ]
        result[f"kamea.mean.{key}"] = (
            round(sum(values) / len(values), 6) if values else 0.0
        )
    return result


__all__ = ["build_structural_measurement", "flatten_metric_means"]
