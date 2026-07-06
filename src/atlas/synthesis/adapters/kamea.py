
"""Kamea evidence adapter.

Converts Kamea identity graph summaries into StructuralEvidence.
"""

from __future__ import annotations

from typing import Any

from atlas.synthesis.evidence import StructuralEvidence
from atlas.synthesis.adapters.utils import make_record, safe_dict, safe_float


def collect(payload: dict[str, Any]) -> list[StructuralEvidence]:
    """Collect Kamea evidence from compiled payload."""
    kamea = find_kamea(payload)

    if not kamea:
        return []

    summary = safe_dict(kamea.get("summary"))
    evidence: list[StructuralEvidence] = []

    node_count = safe_float(summary.get("node_count"))
    edge_count = safe_float(summary.get("edge_count"))
    repeated_node_count = safe_float(summary.get("repeated_node_count"))
    multi_cipher_node_count = safe_float(summary.get("multi_cipher_node_count"))
    multi_planet_node_count = safe_float(summary.get("multi_planet_node_count"))
    max_node_weight = safe_float(summary.get("max_node_weight"))
    max_edge_weight = safe_float(summary.get("max_edge_weight"))
    construction_pass_count = safe_float(summary.get("construction_pass_count"))

    density = edge_count / max(node_count, 1.0)
    repeat_ratio = repeated_node_count / max(node_count, 1.0)
    multi_cipher_ratio = multi_cipher_node_count / max(node_count, 1.0)
    multi_planet_ratio = multi_planet_node_count / max(node_count, 1.0)

    if construction_pass_count >= 21:
        evidence.append(make_record("kamea.identity_graph", "symbolic_coherence", construction_pass_count, 0.78))

    if density >= 2.0:
        evidence.append(make_record("kamea.identity_graph", "high_graph_complexity", density, 0.76))

    if repeat_ratio >= 0.40:
        evidence.append(make_record("kamea.identity_graph", "recursive_patterning", repeat_ratio, 0.80))

    if multi_cipher_ratio >= 0.30:
        evidence.append(make_record("kamea.identity_graph", "reduction_stability", multi_cipher_ratio, 0.76))

    if multi_planet_ratio >= 0.20:
        evidence.append(make_record("kamea.identity_graph", "symbolic_coherence", multi_planet_ratio, 0.74))

    if max_node_weight >= 8:
        evidence.append(make_record("kamea.identity_graph", "persistent_architecture", max_node_weight, 0.78))

    if max_edge_weight >= 3:
        evidence.append(make_record("kamea.identity_graph", "constraint_pattern", max_edge_weight, 0.72))

    evidence.extend(planetary_kamea_evidence(summary))

    return evidence


def find_kamea(payload: dict[str, Any]) -> dict[str, Any]:
    """Find Kamea graph data across known payload shapes."""
    candidates = [
        payload.get("kamea"),
        payload.get("kamea_identity_graph"),
        safe_dict(payload.get("graph")).get("kamea"),
        safe_dict(payload.get("graph")).get("kamea_identity_graph"),
        safe_dict(payload.get("identity_graph")).get("kamea"),
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            if candidate.get("summary") or candidate.get("nodes") or candidate.get("edges"):
                return candidate

    return {}


def planetary_kamea_evidence(summary: dict[str, Any]) -> list[StructuralEvidence]:
    """Create evidence from per-planet Kamea distribution."""
    planets = safe_dict(summary.get("planets"))

    if not planets:
        return []

    evidence: list[StructuralEvidence] = []

    ranked = sorted(
        (
            (str(planet), safe_float(count))
            for planet, count in planets.items()
        ),
        key=lambda item: item[1],
        reverse=True,
    )

    if not ranked:
        return evidence

    dominant_planet, dominant_count = ranked[0]
    total = sum(count for _planet, count in ranked) or 1.0
    dominance = dominant_count / total

    if dominance >= 0.25:
        feature = planet_to_feature(dominant_planet)
        evidence.append(
            make_record(
                f"kamea.planet.{dominant_planet}",
                feature,
                {
                    "planet": dominant_planet,
                    "count": dominant_count,
                    "dominance": round(dominance, 6),
                },
                0.72,
            )
        )

    if len(ranked) >= 5:
        evidence.append(make_record("kamea.planetary_distribution", "distributed_integration", len(ranked), 0.68))

    return evidence


def planet_to_feature(planet: str) -> str:
    """Map Kamea planet to synthesis feature."""
    mapping = {
        "saturn": "constraint_pattern",
        "jupiter": "expansion_pattern",
        "mars": "energy_allocation",
        "sun": "visible_authorship",
        "venus": "value_selection",
        "mercury": "information_routing",
        "moon": "internal_stabilization",
    }

    return mapping.get(str(planet).lower(), "symbolic_coherence")
