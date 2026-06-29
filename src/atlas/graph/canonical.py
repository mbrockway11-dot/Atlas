"""Canonical Identity Graph orchestration.

The Canonical Identity Graph (CIG) is the authoritative graph-native
representation of one Atlas identity.

It is built from:

21 construction layers
    -> one merged IdentityGraph
    -> structural analysis
    -> coherence field
    -> structural reduction
    -> structural attractor
    -> topology signature

The CIG is the graph-space foundation for identity comparison.
Feature vectors are downstream summaries, not the canonical object.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from atlas.graph.analysis import analyze_identity_graph
from atlas.graph.attractor import extract_structural_attractor
from atlas.graph.coherence import compute_coherence_field
from atlas.graph.identity_graph import build_identity_graph_v2
from atlas.graph.reduction import reduce_identity_graph
from atlas.topology.topology_signature import (
    TopologySignature,
    build_topology_signature,
    topology_signature_to_dict,
)


CIG_VERSION = "1.0"


@dataclass(frozen=True)
class CanonicalIdentityGraph:
    """Canonical graph-native identity representation."""

    version: str
    name: str
    raw_graph: dict[str, Any]
    analyzed_graph: dict[str, Any]
    coherence_graph: dict[str, Any]
    reduced_graph: dict[str, Any]
    structural_attractor: dict[str, Any]
    topology_signature: TopologySignature
    summary: dict[str, Any]


def build_canonical_identity_graph(acf: dict[str, Any]) -> CanonicalIdentityGraph:
    """Build the Canonical Identity Graph from an ACF profile.

    This is the primary Atlas graph-native identity pipeline.
    """
    raw_graph = build_identity_graph_v2(acf)
    analyzed_graph = analyze_identity_graph(raw_graph)
    coherence_graph = compute_coherence_field(analyzed_graph)
    reduced_graph = reduce_identity_graph(coherence_graph)
    structural_attractor = extract_structural_attractor(reduced_graph)

    attractor_graph = structural_attractor["graph"]
    topology_signature = build_topology_signature(attractor_graph)

    summary = build_cig_summary(
        raw_graph=raw_graph,
        analyzed_graph=analyzed_graph,
        coherence_graph=coherence_graph,
        reduced_graph=reduced_graph,
        structural_attractor=structural_attractor,
        topology_signature=topology_signature,
    )

    return CanonicalIdentityGraph(
        version=CIG_VERSION,
        name=acf["identity"]["name"],
        raw_graph=raw_graph,
        analyzed_graph=analyzed_graph,
        coherence_graph=coherence_graph,
        reduced_graph=reduced_graph,
        structural_attractor=structural_attractor,
        topology_signature=topology_signature,
        summary=summary,
    )


def build_cig_summary(
    *,
    raw_graph: dict[str, Any],
    analyzed_graph: dict[str, Any],
    coherence_graph: dict[str, Any],
    reduced_graph: dict[str, Any],
    structural_attractor: dict[str, Any],
    topology_signature: TopologySignature,
) -> dict[str, Any]:
    """Build top-level CIG summary."""
    raw_node_count = len(raw_graph.get("nodes", {}))
    raw_edge_count = len(raw_graph.get("edges", {}))

    reduced_node_count = len(reduced_graph.get("nodes", {}))
    reduced_edge_count = len(reduced_graph.get("edges", {}))

    attractor_summary = structural_attractor.get("summary", {})

    return {
        "version": CIG_VERSION,
        "definition": (
            "Canonical graph-native identity representation derived from "
            "all 21 Atlas construction layers."
        ),
        "construction_pass_count": len(raw_graph.get("construction_passes", [])),
        "raw_node_count": raw_node_count,
        "raw_edge_count": raw_edge_count,
        "analyzed_component_count": analyzed_graph.get("analysis", {}).get(
            "component_count",
            0,
        ),
        "coherence_core_node_count": coherence_graph.get("coherence", {}).get(
            "core_node_count",
            0,
        ),
        "reduced_node_count": reduced_node_count,
        "reduced_edge_count": reduced_edge_count,
        "removed_node_count": raw_node_count - reduced_node_count,
        "removed_edge_count": raw_edge_count - reduced_edge_count,
        "node_retention_ratio": _ratio(reduced_node_count, raw_node_count),
        "edge_retention_ratio": _ratio(reduced_edge_count, raw_edge_count),
        "attractor_node_count": attractor_summary.get("node_count", 0),
        "attractor_edge_count": attractor_summary.get("edge_count", 0),
        "attractor_node_retention_ratio": attractor_summary.get(
            "node_retention_ratio",
            0.0,
        ),
        "attractor_edge_retention_ratio": attractor_summary.get(
            "edge_retention_ratio",
            0.0,
        ),
        "attractor_density": attractor_summary.get("density", 0.0),
        "attractor_bridge_count": attractor_summary.get("bridge_count", 0),
        "attractor_articulation_point_count": attractor_summary.get(
            "articulation_point_count",
            0,
        ),
        "signature_node_count": topology_signature.node_count,
        "signature_edge_count": topology_signature.edge_count,
        "signature_density": topology_signature.density,
        "signature_average_degree": topology_signature.average_degree,
    }


def canonical_identity_graph_to_dict(
    cig: CanonicalIdentityGraph,
) -> dict[str, Any]:
    """Convert CIG to JSON-safe dictionary."""
    output = asdict(cig)
    output["topology_signature"] = topology_signature_to_dict(
        cig.topology_signature,
    )
    return output


def _ratio(numerator: float, denominator: float) -> float:
    """Return safe rounded ratio."""
    if denominator == 0:
        return 0.0

    return round(float(numerator) / float(denominator), 6)