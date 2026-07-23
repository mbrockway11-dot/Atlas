"""Graph-of-graphs assembly for the astronomy-first CSS."""

from __future__ import annotations

from typing import Any

from atlas.astronomy import CLASSICAL_KAMEA_BODIES


STRUCTURAL_MEASUREMENT_VERSION = "1.1.0"


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
        projection = bodies[body].get("symbolic_projection", {})
        historically_supported = body in CLASSICAL_KAMEA_BODIES
        nodes.append({
            "node_id": body,
            "node_type": (
                "astronomical_kamea_node"
                if historically_supported
                else "astronomical_only_node"
            ),
            "astronomy_ref": f"astronomy.measurements.bodies.{body}",
            "kamea_graph_ref": f"kamea.normalized_graphs.{body.casefold()}"
            if kamea else None,
            "kamea_graph_available": bool(kamea),
            "symbolic_projection": projection,
            "astronomical_metadata": select_astronomical_metadata(bodies[body]),
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
            "normalized_orb_strength": row.get(
                "normalized_orb_strength",
                row["orb_strength"],
            ),
            "applying_separating": row.get("applying_separating"),
            "weight": row["orb_strength"],
        }
        for row in aspect_graph.get("edges", [])
    ]
    feature_vector = flatten_metric_means(normalized_kamea_graphs)
    feature_vector.update({
        "astronomy.body_count": float(len(bodies)),
        "astronomy.aspect_edge_count": float(len(edges)),
    })
    result = {
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
        "astronomical_similarity": {
            "status": "pending_population_reference_corpus",
            "feature_scope": "measured_astronomical_metadata",
        },
        "classical_kamea_similarity": {
            "status": "pending_population_reference_corpus",
            "feature_scope": "seven_historical_classical_kamea_graphs",
        },
        "combined_multilayer_similarity": {
            "status": "pending_population_reference_corpus",
            "feature_scope": "astronomy_plus_available_classical_kamea",
            "missing_outer_planet_kamea_penalty": 0.0,
        },
        "cluster_membership": {"status": "pending_population_fit"},
        "canonical_transform_policy": {
            "outer_planet_symbolic_transforms": (
                "disabled_not_in_canonical_pipeline"
            ),
            "interpretive_operators_executed": [],
            "kamea_graph_mutation_by_astronomy": False,
        },
        "interpretation_applied": False,
    }
    from atlas.css_schema import validate_multiscale_css

    result["schema_validation"] = validate_multiscale_css(
        astronomy=astronomy,
        normalized_kamea_graphs=normalized_kamea_graphs,
        structural_measurement=result,
    )
    return result


def select_astronomical_metadata(measurement: dict[str, Any]) -> dict[str, Any]:
    """Carry measured node metadata without importing symbolic operators."""
    keys = (
        "apparent_longitude_velocity_deg_per_day",
        "retrograde",
        "iau_constellation",
        "iau_constellation_abbreviation",
        "tropical_sign",
        "sidereal_lahiri_sign",
        "tropical_coordinates",
        "sidereal_lahiri_coordinates",
        "ecliptic_longitude_degrees",
        "ecliptic_latitude_degrees",
        "distance_au",
    )
    return {
        key: measurement.get(key)
        for key in keys
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


__all__ = [
    "build_structural_measurement",
    "flatten_metric_means",
    "select_astronomical_metadata",
]
