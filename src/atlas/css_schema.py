"""Schema validation for the heterogeneous astronomy-first CSS."""

from __future__ import annotations

from typing import Any

from atlas.astronomy import (
    ASTRONOMY_ONLY_BODIES,
    CANONICAL_BODIES,
    CLASSICAL_KAMEA_BODIES,
)


MULTISCALE_CSS_SCHEMA_VERSION = "atlas.astronomy-first-css.v1.1"


def validate_multiscale_css(
    *,
    astronomy: dict[str, Any],
    normalized_kamea_graphs: dict[str, Any],
    structural_measurement: dict[str, Any],
) -> dict[str, Any]:
    """Validate body, projection, graph, similarity, and operator contracts."""
    errors: list[str] = []
    warnings: list[str] = []
    bodies = astronomy.get("bodies", {}) or {}
    graph_keys = {str(key).casefold() for key in normalized_kamea_graphs}
    expected_classical = {body.casefold() for body in CLASSICAL_KAMEA_BODIES}
    master_graph = structural_measurement.get("master_graph", {}) or {}
    master_nodes = {
        row.get("node_id"): row
        for row in master_graph.get("nodes", [])
        if isinstance(row, dict)
    }

    if tuple(bodies) != CANONICAL_BODIES:
        errors.append("astronomy_must_preserve_canonical_ten_body_order")
    if set(bodies) != set(CANONICAL_BODIES):
        errors.append("astronomy_body_set_must_equal_canonical_ten")
    if graph_keys - expected_classical:
        errors.append("nonclassical_kamea_projection_forbidden")
    if graph_keys != expected_classical:
        errors.append("exactly_seven_classical_kamea_graphs_required")

    for body in CLASSICAL_KAMEA_BODIES:
        projection = (bodies.get(body) or {}).get("symbolic_projection", {})
        if projection.get("available") is not True:
            errors.append(f"{body}:classical_symbolic_projection_must_be_available")
        node = master_nodes.get(body, {})
        if node.get("node_type") != "astronomical_kamea_node":
            errors.append(f"{body}:invalid_master_node_type")

    for body in ASTRONOMY_ONLY_BODIES:
        projection = (bodies.get(body) or {}).get("symbolic_projection", {})
        if projection.get("available") is not False:
            errors.append(f"{body}:symbolic_projection_must_be_unavailable")
        if projection.get("reason") != "no_historical_classical_kamea":
            errors.append(f"{body}:invalid_symbolic_projection_reason")
        node = master_nodes.get(body, {})
        if node.get("node_type") != "astronomical_only_node":
            errors.append(f"{body}:invalid_master_node_type")
        if node.get("kamea_graph_available") is not False:
            errors.append(f"{body}:kamea_graph_must_be_unavailable")

    if set(master_nodes) != set(CANONICAL_BODIES):
        errors.append("master_graph_must_contain_all_ten_astronomical_bodies")

    for field in (
        "astronomical_similarity",
        "classical_kamea_similarity",
        "combined_multilayer_similarity",
    ):
        if field not in structural_measurement:
            errors.append(f"missing_similarity_channel:{field}")

    policy = structural_measurement.get("canonical_transform_policy", {}) or {}
    if policy.get("interpretive_operators_executed") != []:
        errors.append("canonical_measurement_executed_interpretive_operator")
    if policy.get("kamea_graph_mutation_by_astronomy") is not False:
        errors.append("astronomy_must_not_mutate_kamea_graphs")
    if structural_measurement.get("interpretation_applied") is not False:
        errors.append("canonical_measurement_must_be_interpretation_free")

    return {
        "success": not errors,
        "schema_version": MULTISCALE_CSS_SCHEMA_VERSION,
        "errors": errors,
        "warnings": warnings,
        "checks": {
            "astronomical_body_count": len(bodies),
            "classical_kamea_graph_count": len(graph_keys & expected_classical),
            "astronomy_only_body_count": len(ASTRONOMY_ONLY_BODIES),
            "mixed_node_types_supported": {
                row.get("node_type")
                for row in master_nodes.values()
            } == {
                "astronomical_kamea_node",
                "astronomical_only_node",
            },
            "missing_outer_planet_kamea_is_valid": not bool(
                graph_keys & {body.casefold() for body in ASTRONOMY_ONLY_BODIES}
            ),
            "interpretive_operator_count": len(
                policy.get("interpretive_operators_executed", [])
            ),
        },
        "profile_validity": {
            "outer_planet_kamea_required": False,
            "missing_outer_planet_kamea_penalty": 0.0,
        },
    }


__all__ = [
    "MULTISCALE_CSS_SCHEMA_VERSION",
    "validate_multiscale_css",
]
