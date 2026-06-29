"""Identity Graph Stack orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from atlas.graph.canonical import (
    CanonicalIdentityGraph,
    build_canonical_identity_graph,
    canonical_identity_graph_to_dict,
)
from atlas.graph.identity_resonance import (
    IdentityResonance,
    build_identity_resonance,
    identity_resonance_to_dict,
)
from atlas.graph.identity_topology import (
    IdentityTopology,
    build_identity_topology,
    identity_topology_to_dict,
)
from atlas.graph.motifs import (
    StructuralMotifs,
    extract_structural_motifs,
    structural_motifs_to_dict,
)
from atlas.graph.structural_genome import (
    StructuralGenome,
    build_structural_genome,
    structural_genome_to_dict,
)
from atlas.graph.structural_truth import (
    StructuralTruthGraph,
    build_structural_truth_graph,
    structural_truth_graph_to_dict,
)


STACK_VERSION = "1.0"


@dataclass(frozen=True)
class IdentityGraphStack:
    """Full graph-native Atlas identity package."""

    version: str
    name: str
    cig: CanonicalIdentityGraph
    stg: StructuralTruthGraph
    motifs: StructuralMotifs
    genome: StructuralGenome
    topology: IdentityTopology
    resonance: IdentityResonance
    summary: dict[str, Any]


def build_identity_graph_stack(acf: dict[str, Any]) -> IdentityGraphStack:
    """Build the complete graph-native identity stack from an ACF profile."""
    cig = build_canonical_identity_graph(acf)
    stg = build_structural_truth_graph(cig)

    motif_graph = {
        "nodes": stg.nodes,
        "edges": stg.edges,
    }
    motifs = extract_structural_motifs(motif_graph)

    genome = build_structural_genome(stg)
    topology = build_identity_topology(genome)
    resonance = build_identity_resonance(topology)

    summary = build_stack_summary(
        cig=cig,
        stg=stg,
        motifs=motifs,
        genome=genome,
        topology=topology,
        resonance=resonance,
    )

    return IdentityGraphStack(
        version=STACK_VERSION,
        name=cig.name,
        cig=cig,
        stg=stg,
        motifs=motifs,
        genome=genome,
        topology=topology,
        resonance=resonance,
        summary=summary,
    )


def build_stack_summary(
    *,
    cig: CanonicalIdentityGraph,
    stg: StructuralTruthGraph,
    motifs: StructuralMotifs,
    genome: StructuralGenome,
    topology: IdentityTopology,
    resonance: IdentityResonance,
) -> dict[str, Any]:
    """Build top-level stack summary."""
    return {
        "version": STACK_VERSION,
        "definition": (
            "Complete graph-native Atlas identity stack: CIG, STG, motifs, "
            "genome, topology, and resonance."
        ),
        "name": cig.name,
        "cig_version": cig.version,
        "stg_version": stg.version,
        "motif_version": motifs.version,
        "genome_version": genome.version,
        "topology_version": topology.version,
        "resonance_version": resonance.version,
        "raw_node_count": cig.summary.get("raw_node_count", 0),
        "raw_edge_count": cig.summary.get("raw_edge_count", 0),
        "truth_node_count": stg.summary.get("truth_node_count", 0),
        "truth_edge_count": stg.summary.get("truth_edge_count", 0),
        "motif_richness": genome.motif_richness,
        "dominant_motif": genome.summary.get("dominant_motif"),
        "topology_class": topology.topology_class,
        "dominant_topology_axis": topology.dominant_axis,
        "resonance_class": resonance.resonance_class,
        "dominant_resonance_axis": resonance.dominant_resonance_axis,
    }


def identity_graph_stack_to_dict(
    stack: IdentityGraphStack,
) -> dict[str, Any]:
    """Convert IdentityGraphStack to JSON-safe dictionary."""
    return {
        "version": stack.version,
        "name": stack.name,
        "cig": canonical_identity_graph_to_dict(stack.cig),
        "stg": structural_truth_graph_to_dict(stack.stg),
        "motifs": structural_motifs_to_dict(stack.motifs),
        "genome": structural_genome_to_dict(stack.genome),
        "topology": identity_topology_to_dict(stack.topology),
        "resonance": identity_resonance_to_dict(stack.resonance),
        "summary": dict(stack.summary),
    }