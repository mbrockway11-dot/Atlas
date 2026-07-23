"""Pairwise confluence comparison for invariant Kamea riverbeds."""

from __future__ import annotations

from typing import Any

from atlas.kamea_flow.shape import compare_unified_shape_fields


CONFLUENCE_VERSION = "1.0.0"


def build_riverbed_confluence(
    profile_a: str,
    report_a: dict[str, Any],
    profile_b: str,
    report_b: dict[str, Any],
) -> dict[str, Any]:
    rows_a = _planet_map(report_a)
    rows_b = _planet_map(report_b)
    planets = sorted(set(rows_a) | set(rows_b))
    comparisons = [
        _compare_planet(planet, rows_a.get(planet, {}), rows_b.get(planet, {}))
        for planet in planets
    ]
    shape_confluence = compare_unified_shape_fields(report_a.get("shape", {}), report_b.get("shape", {}))
    return {
        "success": True,
        "version": CONFLUENCE_VERSION,
        "profile_a": profile_a,
        "profile_b": profile_b,
        "definition": "Overlap and divergence between independently derived invariant planetary riverbeds.",
        "claim_type": "deterministic_symbolic_comparison",
        "causal_claim": False,
        "planetary_confluences": comparisons,
        "shape_confluence": shape_confluence,
        "summary": {
            "planet_count": len(comparisons),
            "shared_invariant_node_count": sum(row["shared_node_count"] for row in comparisons),
            "shared_invariant_edge_count": sum(row["shared_edge_count"] for row in comparisons),
            "opposing_current_count": sum(row["opposing_current_count"] for row in comparisons),
            "mean_node_jaccard": _mean(row["node_jaccard"] for row in comparisons),
            "mean_edge_jaccard": _mean(row["edge_jaccard"] for row in comparisons),
            "strongest_confluence_planet": _strongest(comparisons),
            "mean_normalized_shape_jaccard": shape_confluence["mean_consensus_shape_jaccard"],
            "mean_normalized_directional_jaccard": shape_confluence["mean_directional_shape_jaccard"],
            "strongest_shape_confluence_planet": shape_confluence["strongest_shape_confluence_planet"],
        },
    }


def _planet_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("planet")): row
        for row in report.get("riverbed", {}).get("planetary_riverbeds", []) or []
    }


def _compare_planet(planet: str, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_nodes = {str(row.get("node")) for row in left.get("invariant_nodes", []) or []}
    right_nodes = {str(row.get("node")) for row in right.get("invariant_nodes", []) or []}
    left_edges = {(str(row.get("source")), str(row.get("target"))) for row in left.get("invariant_edges", []) or []}
    right_edges = {(str(row.get("source")), str(row.get("target"))) for row in right.get("invariant_edges", []) or []}
    opposing = sorted(left_edges & {(target, source) for source, target in right_edges})
    return {
        "planet": planet,
        "shared_nodes": sorted(left_nodes & right_nodes),
        "profile_a_only_nodes": sorted(left_nodes - right_nodes),
        "profile_b_only_nodes": sorted(right_nodes - left_nodes),
        "shared_edges": _edge_rows(left_edges & right_edges),
        "profile_a_only_edges": _edge_rows(left_edges - right_edges),
        "profile_b_only_edges": _edge_rows(right_edges - left_edges),
        "opposing_currents": _edge_rows(set(opposing)),
        "shared_node_count": len(left_nodes & right_nodes),
        "shared_edge_count": len(left_edges & right_edges),
        "opposing_current_count": len(opposing),
        "node_jaccard": _jaccard(left_nodes, right_nodes),
        "edge_jaccard": _jaccard(left_edges, right_edges),
    }


def _edge_rows(edges: set[tuple[str, str]]) -> list[dict[str, str]]:
    return [{"source": source, "target": target} for source, target in sorted(edges)]


def _jaccard(left: set[Any], right: set[Any]) -> float:
    union = left | right
    return round(len(left & right) / len(union), 6) if union else 0.0


def _mean(values: Any) -> float:
    items = [float(value) for value in values]
    return round(sum(items) / len(items), 6) if items else 0.0


def _strongest(rows: list[dict[str, Any]]) -> str | None:
    return max(rows, key=lambda row: (row["node_jaccard"] + row["edge_jaccard"], row["planet"]))["planet"] if rows else None
