
"""Behavior evidence adapter.

Translates structural signatures into observable behavioral hypotheses.
"""

from __future__ import annotations

from typing import Any

from atlas.synthesis.evidence import StructuralEvidence
from atlas.synthesis.adapters.utils import make_record, safe_dict, safe_float


def collect(payload: dict[str, Any]) -> list[StructuralEvidence]:
    """Collect behavior evidence from graph, classification, topology, and resonance."""
    evidence: list[StructuralEvidence] = []

    classification = safe_dict(payload.get("classification"))
    graph = safe_dict(payload.get("graph"))
    graph_summary = safe_dict(graph.get("summary"))
    topology = safe_dict(payload.get("topology"))
    topology_summary = safe_dict(topology.get("summary"))
    topology_vector = safe_dict(topology_summary.get("topology_vector"))
    resonance = safe_dict(payload.get("resonance"))
    resonance_summary = safe_dict(resonance.get("summary"))
    resonance_vector = safe_dict(resonance_summary.get("resonance_vector"))

    role = classification.get("structural_role", "")
    topology_class = graph_summary.get("topology_class", "")
    axis = graph_summary.get("dominant_topology_axis", "")
    motif_richness = safe_float(graph_summary.get("motif_richness"))
    raw_edges = safe_float(graph_summary.get("raw_edge_count"))
    raw_nodes = safe_float(graph_summary.get("raw_node_count"))
    truth_edges = safe_float(graph_summary.get("truth_edge_count"))
    truth_nodes = safe_float(graph_summary.get("truth_node_count"))

    raw_density = raw_edges / max(raw_nodes, 1.0)
    truth_density = truth_edges / max(truth_nodes, 1.0)

    if role == "Persistence-Architect" or axis == "persistence":
        evidence.append(make_record("behavior.role", "long_horizon_planning", role or axis, 0.86))
        evidence.append(make_record("behavior.role", "durable_system_construction", role or axis, 0.88))
        evidence.append(make_record("behavior.role", "continuity_preservation", role or axis, 0.84))

    if role == "Cycle-Weaver" or motif_richness >= 0.65:
        evidence.append(make_record("behavior.role", "recurrence_detection", motif_richness, 0.84))
        evidence.append(make_record("behavior.role", "iterative_refinement", motif_richness, 0.82))

    if role == "Connector-Architect" or "distributed" in str(topology_class):
        evidence.append(make_record("behavior.role", "cross_domain_linking", topology_class, 0.84))
        evidence.append(make_record("behavior.role", "parallel_context_management", topology_class, 0.80))

    if role == "Amplifier-Connector":
        evidence.append(make_record("behavior.role", "signal_amplification", role, 0.82))
        evidence.append(make_record("behavior.role", "expressive_catalysis", role, 0.80))

    if role == "Pattern-Weaver" or truth_density >= 1.0:
        evidence.append(make_record("behavior.role", "pattern_compression", truth_density, 0.86))
        evidence.append(make_record("behavior.role", "high_resolution_discrimination", truth_density, 0.84))

    if raw_density >= 4.0:
        evidence.append(make_record("behavior.graph", "complexity_tolerance", raw_density, 0.84))

    if truth_density >= 1.0:
        evidence.append(make_record("behavior.graph", "structural_selectivity", truth_density, 0.86))

    if truth_density <= 0.25:
        evidence.append(make_record("behavior.graph", "aggressive_compression", truth_density, 0.78))

    if safe_float(topology_vector.get("branching")) >= 0.5:
        evidence.append(make_record("behavior.topology", "branching_decision_style", topology_vector.get("branching"), 0.78))

    if safe_float(topology_vector.get("bottleneck")) >= 0.5:
        evidence.append(make_record("behavior.topology", "constraint_sensitive_execution", topology_vector.get("bottleneck"), 0.80))

    if safe_float(resonance_vector.get("stability")) >= 0.5:
        evidence.append(make_record("behavior.resonance", "stability_seeking", resonance_vector.get("stability"), 0.80))

    if safe_float(resonance_vector.get("propagation")) >= 0.5:
        evidence.append(make_record("behavior.resonance", "message_propagation", resonance_vector.get("propagation"), 0.78))

    if safe_float(resonance_vector.get("activation")) >= 0.5:
        evidence.append(make_record("behavior.resonance", "activation_driven_action", resonance_vector.get("activation"), 0.76))

    return evidence
