"""Structural Truth Graph extraction.

The Structural Truth Graph (STG) is the pruned, high-confidence identity
skeleton derived from the Canonical Identity Graph.

CIG = full canonical graph pipeline.
STG = retained structural truth layer from the reduced attractor graph.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from atlas.graph.canonical import CanonicalIdentityGraph


STG_VERSION = "1.0"


@dataclass(frozen=True)
class StructuralTruthGraph:
    """Pruned structural truth graph for one identity."""

    version: str
    name: str
    nodes: dict[str, dict[str, Any]]
    edges: dict[str, dict[str, Any]]
    summary: dict[str, Any]


def build_structural_truth_graph(
    cig: CanonicalIdentityGraph,
    *,
    min_node_truth_score: float = 0.35,
    min_edge_truth_score: float = 0.25,
) -> StructuralTruthGraph:
    """Build the Structural Truth Graph from a Canonical Identity Graph."""
    source_graph = cig.structural_attractor["graph"]

    scored_nodes = {
        node_id: {
            **dict(node),
            "truth": compute_node_truth(node),
        }
        for node_id, node in source_graph.get("nodes", {}).items()
    }

    retained_nodes = {
        node_id: node
        for node_id, node in scored_nodes.items()
        if node["truth"]["score"] >= min_node_truth_score
    }

    scored_edges = {
        edge_id: {
            **dict(edge),
            "truth": compute_edge_truth(edge),
        }
        for edge_id, edge in source_graph.get("edges", {}).items()
    }

    retained_edges = {
        edge_id: edge
        for edge_id, edge in scored_edges.items()
        if edge["truth"]["score"] >= min_edge_truth_score
        and edge["source"] in retained_nodes
        and edge["target"] in retained_nodes
    }

    summary = build_stg_summary(
        cig=cig,
        source_nodes=scored_nodes,
        source_edges=scored_edges,
        retained_nodes=retained_nodes,
        retained_edges=retained_edges,
        min_node_truth_score=min_node_truth_score,
        min_edge_truth_score=min_edge_truth_score,
    )

    return StructuralTruthGraph(
        version=STG_VERSION,
        name=cig.name,
        nodes=retained_nodes,
        edges=retained_edges,
        summary=summary,
    )


def compute_node_truth(node: dict[str, Any]) -> dict[str, Any]:
    """Compute deterministic node truth score."""
    coherence = node.get("coherence", {}).get("score", 0.0)
    construction = normalized(node.get("weight", 0), 21)
    cipher = normalized(node.get("cipher_count", 0), 3)
    planet = normalized(node.get("planet_count", 0), 7)

    role = 0.0

    if node.get("is_hub"):
        role += 0.5

    if node.get("is_articulation"):
        role += 0.5

    role = clamp(role)

    score = (
        coherence * 0.45
        + construction * 0.20
        + cipher * 0.15
        + planet * 0.15
        + role * 0.05
    )

    score = clamp(score)

    return {
        "score": score,
        "class": classify_truth(score),
        "coherence": coherence,
        "construction_support": construction,
        "cipher_support": cipher,
        "planet_support": planet,
        "role_support": role,
    }


def compute_edge_truth(edge: dict[str, Any]) -> dict[str, Any]:
    """Compute deterministic edge truth score."""
    coherence = edge.get("coherence", {}).get("score", 0.0)
    construction = normalized(edge.get("weight", 0), 21)
    cipher = normalized(edge.get("cipher_count", 0), 3)
    planet = normalized(edge.get("planet_count", 0), 7)
    bridge = 1.0 if edge.get("is_bridge") else 0.0

    score = (
        coherence * 0.45
        + construction * 0.20
        + cipher * 0.15
        + planet * 0.15
        + bridge * 0.05
    )

    score = clamp(score)

    return {
        "score": score,
        "class": classify_truth(score),
        "coherence": coherence,
        "construction_support": construction,
        "cipher_support": cipher,
        "planet_support": planet,
        "bridge_support": bridge,
    }


def build_stg_summary(
    *,
    cig: CanonicalIdentityGraph,
    source_nodes: dict[str, dict[str, Any]],
    source_edges: dict[str, dict[str, Any]],
    retained_nodes: dict[str, dict[str, Any]],
    retained_edges: dict[str, dict[str, Any]],
    min_node_truth_score: float,
    min_edge_truth_score: float,
) -> dict[str, Any]:
    """Build Structural Truth Graph summary."""
    return {
        "version": STG_VERSION,
        "definition": (
            "Pruned high-confidence identity skeleton derived from the "
            "Canonical Identity Graph structural attractor."
        ),
        "source": "CanonicalIdentityGraph.structural_attractor.graph",
        "cig_version": cig.version,
        "min_node_truth_score": min_node_truth_score,
        "min_edge_truth_score": min_edge_truth_score,
        "source_node_count": len(source_nodes),
        "source_edge_count": len(source_edges),
        "truth_node_count": len(retained_nodes),
        "truth_edge_count": len(retained_edges),
        "node_retention_ratio": ratio(len(retained_nodes), len(source_nodes)),
        "edge_retention_ratio": ratio(len(retained_edges), len(source_edges)),
        "mean_node_truth": mean_truth(retained_nodes),
        "mean_edge_truth": mean_truth(retained_edges),
        "top_truth_nodes": top_truth_records(retained_nodes),
        "top_truth_edges": top_truth_records(retained_edges),
    }


def structural_truth_graph_to_dict(
    stg: StructuralTruthGraph,
) -> dict[str, Any]:
    """Convert Structural Truth Graph to JSON-safe dictionary."""
    return asdict(stg)


def classify_truth(score: float) -> str:
    """Classify structural truth strength."""
    if score >= 0.70:
        return "core_truth"

    if score >= 0.35:
        return "adaptive_truth"

    return "peripheral"


def top_truth_records(
    records: dict[str, dict[str, Any]],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return highest truth-score records."""
    ranked = sorted(
        records.values(),
        key=lambda record: record.get("truth", {}).get("score", 0.0),
        reverse=True,
    )

    return ranked[:limit]


def mean_truth(records: dict[str, dict[str, Any]]) -> float:
    """Return mean truth score."""
    scores = [
        record.get("truth", {}).get("score", 0.0)
        for record in records.values()
    ]

    if not scores:
        return 0.0

    return sum(scores) / len(scores)


def normalized(value: float, maximum: float) -> float:
    """Normalize to 0-1."""
    if maximum <= 0:
        return 0.0

    return clamp(float(value) / maximum)


def ratio(numerator: float, denominator: float) -> float:
    """Return safe ratio."""
    if denominator == 0:
        return 0.0

    return round(float(numerator) / float(denominator), 6)


def clamp(value: float) -> float:
    """Clamp to 0-1."""
    return max(0.0, min(1.0, float(value)))