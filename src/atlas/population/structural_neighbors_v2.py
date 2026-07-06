
"""Structural Neighbor Engine v2.

Builds explainable nearest-neighbor similarity from canonical structural vectors.
"""

from __future__ import annotations

from math import sqrt
from typing import Any

from atlas.compiler.canonical_profile_compiler import compile_canonical_profile
from atlas.library.profile_library import list_saved_profiles


STRUCTURAL_NEIGHBOR_VERSION = "2.0"


WEIGHTS = {
    "role": 0.20,
    "subtype": 0.10,
    "topology": 0.15,
    "axis": 0.10,
    "motif": 0.05,
    "resonance": 0.05,
    "numeric": 0.35,
}


NUMERIC_FIELDS = [
    "motif_richness",
    "raw_density",
    "truth_density",
    "raw_nodes",
    "raw_edges",
    "truth_nodes",
    "truth_edges",
]


def build_population_vectors(profile_keys: list[str] | None = None) -> list[dict[str, Any]]:
    """Build structural vectors for profile corpus."""
    keys = profile_keys or list_saved_profiles()
    vectors = []

    for key in keys:
        payload = compile_canonical_profile(key, force=False)
        if not payload.get("success"):
            continue
        vectors.append(build_structural_vector(payload))

    return vectors


def build_structural_vector(payload: dict[str, Any]) -> dict[str, Any]:
    """Build one structural vector from canonical payload."""
    cls = payload.get("classification", {})
    basis = cls.get("basis", {})
    graph = payload.get("graph", {}).get("summary", {})

    raw_nodes = int(basis.get("raw_node_count") or graph.get("raw_node_count") or 0)
    raw_edges = int(basis.get("raw_edge_count") or graph.get("raw_edge_count") or 0)
    truth_nodes = int(basis.get("truth_node_count") or graph.get("truth_node_count") or 0)
    truth_edges = int(basis.get("truth_edge_count") or graph.get("truth_edge_count") or 0)

    return {
        "profile_key": payload.get("profile_key"),
        "name": cls.get("name") or payload.get("identity", {}).get("name") or payload.get("profile_key"),
        "role": cls.get("structural_role", "missing"),
        "subtype": cls.get("structural_subtype", "missing"),
        "topology": basis.get("topology_class") or graph.get("topology_class") or "missing",
        "axis": basis.get("dominant_topology_axis") or graph.get("dominant_topology_axis") or "missing",
        "motif": basis.get("dominant_motif") or graph.get("dominant_motif") or "missing",
        "resonance": basis.get("resonance_class") or graph.get("resonance_class") or "missing",
        "resonance_axis": basis.get("dominant_resonance_axis") or graph.get("dominant_resonance_axis") or "missing",
        "motif_richness": float(basis.get("motif_richness") or graph.get("motif_richness") or 0),
        "raw_nodes": raw_nodes,
        "raw_edges": raw_edges,
        "truth_nodes": truth_nodes,
        "truth_edges": truth_edges,
        "raw_density": density(raw_edges, raw_nodes),
        "truth_density": density(truth_edges, truth_nodes),
    }


def find_structural_neighbors(
    profile_key: str,
    *,
    limit: int = 10,
    profile_keys: list[str] | None = None,
) -> dict[str, Any]:
    """Find nearest structural neighbors for a profile."""
    vectors = build_population_vectors(profile_keys)
    target = next((item for item in vectors if item.get("profile_key") == profile_key), None)

    if not target:
        return {
            "success": False,
            "version": STRUCTURAL_NEIGHBOR_VERSION,
            "profile_key": profile_key,
            "errors": [f"profile not found: {profile_key}"],
            "neighbors": [],
        }

    scored = []

    for candidate in vectors:
        if candidate.get("profile_key") == profile_key:
            continue

        scored.append(compare_vectors(target, candidate))

    scored.sort(key=lambda item: item["similarity"], reverse=True)

    return {
        "success": True,
        "version": STRUCTURAL_NEIGHBOR_VERSION,
        "profile_key": profile_key,
        "target": target,
        "limit": limit,
        "neighbors": scored[:limit],
        "metric_weights": WEIGHTS,
    }


def compare_vectors(target: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Compare two structural vectors."""
    categorical = {
        "role": exact_match(target, candidate, "role"),
        "subtype": exact_match(target, candidate, "subtype"),
        "topology": exact_match(target, candidate, "topology"),
        "axis": exact_match(target, candidate, "axis"),
        "motif": exact_match(target, candidate, "motif"),
        "resonance": exact_match(target, candidate, "resonance"),
    }

    numeric_score = numeric_similarity(target, candidate)

    similarity = (
        categorical["role"] * WEIGHTS["role"]
        + categorical["subtype"] * WEIGHTS["subtype"]
        + categorical["topology"] * WEIGHTS["topology"]
        + categorical["axis"] * WEIGHTS["axis"]
        + categorical["motif"] * WEIGHTS["motif"]
        + categorical["resonance"] * WEIGHTS["resonance"]
        + numeric_score * WEIGHTS["numeric"]
    )

    return {
        "profile_key": candidate.get("profile_key"),
        "name": candidate.get("name"),
        "similarity": round(similarity, 6),
        "similarity_percent": round(similarity * 100, 2),
        "candidate": candidate,
        "breakdown": {
            **categorical,
            "numeric": round(numeric_score, 6),
        },
        "shared": shared_features(target, candidate),
        "differences": different_features(target, candidate),
    }


def numeric_similarity(target: dict[str, Any], candidate: dict[str, Any]) -> float:
    """Similarity across numeric graph metrics."""
    distances = []

    for field in NUMERIC_FIELDS:
        a = float(target.get(field) or 0)
        b = float(candidate.get(field) or 0)
        scale = max(abs(a), abs(b), 1.0)
        distances.append(((a - b) / scale) ** 2)

    distance = sqrt(sum(distances) / max(len(distances), 1))
    return max(0.0, 1.0 - distance)


def exact_match(a: dict[str, Any], b: dict[str, Any], field: str) -> float:
    """Return 1 for exact match, else 0."""
    return 1.0 if str(a.get(field)) == str(b.get(field)) else 0.0


def shared_features(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    """Return shared categorical features."""
    output = []

    for field in ["role", "subtype", "topology", "axis", "motif", "resonance", "resonance_axis"]:
        if str(a.get(field)) == str(b.get(field)):
            output.append(f"{field}: {a.get(field)}")

    return output


def different_features(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    """Return differing categorical features."""
    output = []

    for field in ["role", "subtype", "topology", "axis", "motif", "resonance", "resonance_axis"]:
        if str(a.get(field)) != str(b.get(field)):
            output.append(f"{field}: {a.get(field)} -> {b.get(field)}")

    return output


def density(edges: int, nodes: int) -> float:
    """Compute graph density proxy."""
    return round(float(edges) / max(float(nodes), 1.0), 6)
