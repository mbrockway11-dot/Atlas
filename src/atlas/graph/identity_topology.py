"""Identity Topology Engine.

The Identity Topology Engine classifies the behavioral structure of a
Structural Genome. It does not interpret personality. It measures graph-native
topological behavior.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from atlas.graph.structural_genome import StructuralGenome


TOPOLOGY_VERSION = "1.0"


@dataclass(frozen=True)
class IdentityTopology:
    """Topological behavior profile for one identity."""

    version: str
    name: str
    topology_class: str
    dominant_axis: str
    flow_pattern: str
    organization_pattern: str
    stability_pattern: str
    hierarchy_score: float
    branching_score: float
    cyclicity_score: float
    bottleneck_score: float
    persistence_score: float
    topology_vector: dict[str, float]
    summary: dict[str, Any]


def build_identity_topology(
    genome: StructuralGenome,
) -> IdentityTopology:
    """Build Identity Topology from Structural Genome."""
    topology_vector = {
        "hierarchy": genome.hierarchy_score,
        "branching": genome.branching_score,
        "cyclicity": genome.cyclicity_score,
        "bottleneck": genome.bottleneck_score,
        "persistence": genome.persistence_score,
        "motif_richness": genome.motif_richness,
    }

    dominant_axis = max(
        topology_vector,
        key=topology_vector.get,
    )

    topology_class = classify_topology(genome)
    flow_pattern = classify_flow_pattern(genome)
    organization_pattern = classify_organization_pattern(genome)
    stability_pattern = classify_stability_pattern(genome)

    summary = {
        "version": TOPOLOGY_VERSION,
        "definition": (
            "Graph-native topology behavior profile derived from the "
            "Structural Genome."
        ),
        "source": "StructuralGenome",
        "genome_version": genome.version,
        "topology_class": topology_class,
        "dominant_axis": dominant_axis,
        "flow_pattern": flow_pattern,
        "organization_pattern": organization_pattern,
        "stability_pattern": stability_pattern,
        "topology_vector": topology_vector,
    }

    return IdentityTopology(
        version=TOPOLOGY_VERSION,
        name=genome.name,
        topology_class=topology_class,
        dominant_axis=dominant_axis,
        flow_pattern=flow_pattern,
        organization_pattern=organization_pattern,
        stability_pattern=stability_pattern,
        hierarchy_score=genome.hierarchy_score,
        branching_score=genome.branching_score,
        cyclicity_score=genome.cyclicity_score,
        bottleneck_score=genome.bottleneck_score,
        persistence_score=genome.persistence_score,
        topology_vector=topology_vector,
        summary=summary,
    )


def classify_topology(genome: StructuralGenome) -> str:
    """Classify overall topology."""
    if genome.cyclicity_score >= 0.35 and genome.branching_score >= 0.25:
        return "branching_cycle"

    if genome.hierarchy_score >= 0.35 and genome.bottleneck_score >= 0.25:
        return "hierarchical_bottleneck"

    if genome.branching_score >= 0.30:
        return "branching_tree"

    if genome.cyclicity_score >= 0.30:
        return "cyclic_network"

    if genome.bottleneck_score >= 0.25:
        return "bridge_dominant"

    if genome.persistence_score >= 0.60:
        return "stable_core"

    return "distributed_sparse"


def classify_flow_pattern(genome: StructuralGenome) -> str:
    """Classify likely graph flow pattern."""
    if genome.bridge_count > genome.hub_count and genome.bottleneck_score >= 0.20:
        return "channeled"

    if genome.hub_count > 0 and genome.leaf_count >= genome.hub_count:
        return "hub_spoke"

    if genome.cycle_like_count > 0:
        return "recirculating"

    if genome.chain_count > genome.star_count:
        return "linear_chain"

    return "diffuse"


def classify_organization_pattern(genome: StructuralGenome) -> str:
    """Classify organization structure."""
    if genome.star_count > 0 and genome.hub_count > 0:
        return "centralized"

    if genome.triangle_count > 0 or genome.cycle_like_count > 0:
        return "clustered"

    if genome.bridge_count > 0 or genome.articulation_count > 0:
        return "segmented"

    return "distributed"


def classify_stability_pattern(genome: StructuralGenome) -> str:
    """Classify structural stability."""
    if genome.persistence_score >= 0.70:
        return "high_persistence"

    if genome.persistence_score >= 0.45:
        return "moderate_persistence"

    if genome.motif_richness >= 0.50:
        return "motif_supported"

    return "low_persistence"


def identity_topology_to_dict(
    topology: IdentityTopology,
) -> dict[str, Any]:
    """Convert IdentityTopology to JSON-safe dictionary."""
    return asdict(topology)