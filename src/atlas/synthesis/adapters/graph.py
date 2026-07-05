
"""Graph evidence adapter."""

from __future__ import annotations

from typing import Any

from atlas.synthesis.evidence import StructuralEvidence
from atlas.synthesis.adapters.utils import make_record, safe_dict, safe_float


def collect(payload: dict[str, Any]) -> list[StructuralEvidence]:
    """Collect evidence from graph summary."""
    graph = safe_dict(payload.get("graph"))
    summary = safe_dict(graph.get("summary"))

    evidence: list[StructuralEvidence] = []

    raw_edges = safe_float(summary.get("raw_edge_count"))
    raw_nodes = safe_float(summary.get("raw_node_count"))
    truth_edges = safe_float(summary.get("truth_edge_count"))
    truth_nodes = safe_float(summary.get("truth_node_count"))
    motif_richness = safe_float(summary.get("motif_richness"))

    raw_density = raw_edges / max(raw_nodes, 1.0)
    truth_density = truth_edges / max(truth_nodes, 1.0)

    if raw_density >= 4.0:
        evidence.append(make_record("graph.summary", "high_graph_complexity", raw_density, 0.86))
    elif raw_density <= 2.0:
        evidence.append(make_record("graph.summary", "low_graph_complexity", raw_density, 0.72))

    if truth_density >= 1.0:
        evidence.append(make_record("graph.summary", "high_truth_density", truth_density, 0.90))
    elif truth_density <= 0.25:
        evidence.append(make_record("graph.summary", "low_truth_density", truth_density, 0.78))

    if motif_richness >= 0.65:
        evidence.append(make_record("graph.motifs", "recursive_patterning", motif_richness, 0.84))

    topology_class = str(summary.get("topology_class", ""))

    if "distributed" in topology_class:
        evidence.append(make_record("graph.topology", "distributed_integration", topology_class, 0.82))

    if "cycle" in topology_class:
        evidence.append(make_record("graph.topology", "recursive_patterning", topology_class, 0.82))

    if summary.get("dominant_topology_axis") == "persistence":
        evidence.append(make_record("graph.topology", "persistent_architecture", True, 0.88))

    return evidence
