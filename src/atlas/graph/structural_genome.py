"""Structural Genome Engine.

The Structural Genome is a compact graph-native identity sequence derived from
the Structural Truth Graph and Structural Motif Engine.

It does not interpret meaning. It summarizes persistent topology.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from atlas.graph.motifs import StructuralMotifs, extract_structural_motifs
from atlas.graph.structural_truth import StructuralTruthGraph


GENOME_VERSION = "1.0"


@dataclass(frozen=True)
class StructuralGenome:
    """Compact structural genome for one identity graph."""

    version: str
    name: str
    node_count: int
    edge_count: int
    hub_count: int
    bridge_count: int
    articulation_count: int
    leaf_count: int
    chain_count: int
    triangle_count: int
    star_count: int
    bottleneck_count: int
    cycle_like_count: int
    motif_richness: float
    hierarchy_score: float
    branching_score: float
    cyclicity_score: float
    bottleneck_score: float
    persistence_score: float
    genome_sequence: tuple[str, ...]
    summary: dict[str, Any]


def build_structural_genome(
    stg: StructuralTruthGraph,
) -> StructuralGenome:
    """Build a Structural Genome from a Structural Truth Graph."""
    graph = {
        "nodes": stg.nodes,
        "edges": stg.edges,
    }

    motifs = extract_structural_motifs(graph)

    hierarchy_score = compute_hierarchy_score(motifs)
    branching_score = compute_branching_score(motifs)
    cyclicity_score = compute_cyclicity_score(motifs)
    bottleneck_score = compute_bottleneck_score(motifs)
    persistence_score = compute_persistence_score(stg)

    genome_sequence = build_genome_sequence(
        motifs=motifs,
        hierarchy_score=hierarchy_score,
        branching_score=branching_score,
        cyclicity_score=cyclicity_score,
        bottleneck_score=bottleneck_score,
        persistence_score=persistence_score,
    )

    summary = build_genome_summary(
        stg=stg,
        motifs=motifs,
        hierarchy_score=hierarchy_score,
        branching_score=branching_score,
        cyclicity_score=cyclicity_score,
        bottleneck_score=bottleneck_score,
        persistence_score=persistence_score,
        genome_sequence=genome_sequence,
    )

    return StructuralGenome(
        version=GENOME_VERSION,
        name=stg.name,
        node_count=motifs.node_count,
        edge_count=motifs.edge_count,
        hub_count=len(motifs.hub_nodes),
        bridge_count=len(motifs.bridge_edges),
        articulation_count=len(motifs.articulation_nodes),
        leaf_count=len(motifs.leaf_nodes),
        chain_count=motifs.chain_count,
        triangle_count=motifs.triangle_count,
        star_count=motifs.star_count,
        bottleneck_count=motifs.bottleneck_count,
        cycle_like_count=motifs.cycle_like_count,
        motif_richness=motifs.summary["motif_richness"],
        hierarchy_score=hierarchy_score,
        branching_score=branching_score,
        cyclicity_score=cyclicity_score,
        bottleneck_score=bottleneck_score,
        persistence_score=persistence_score,
        genome_sequence=genome_sequence,
        summary=summary,
    )


def compute_hierarchy_score(motifs: StructuralMotifs) -> float:
    """Estimate hierarchy from hubs, leaves, and bottlenecks."""
    if motifs.node_count == 0:
        return 0.0

    hub_component = ratio(len(motifs.hub_nodes), motifs.node_count)
    leaf_component = ratio(len(motifs.leaf_nodes), motifs.node_count)
    bottleneck_component = ratio(motifs.bottleneck_count, motifs.node_count + motifs.edge_count)

    return clamp(
        hub_component * 0.35
        + leaf_component * 0.25
        + bottleneck_component * 0.40
    )


def compute_branching_score(motifs: StructuralMotifs) -> float:
    """Estimate branching from stars, hubs, and leaves."""
    if motifs.node_count == 0:
        return 0.0

    return clamp(
        ratio(motifs.star_count, motifs.node_count) * 0.45
        + ratio(len(motifs.hub_nodes), motifs.node_count) * 0.30
        + ratio(len(motifs.leaf_nodes), motifs.node_count) * 0.25
    )


def compute_cyclicity_score(motifs: StructuralMotifs) -> float:
    """Estimate cyclic structure."""
    if motifs.edge_count == 0:
        return 0.0

    return clamp(
        ratio(motifs.cycle_like_count, motifs.edge_count) * 0.65
        + ratio(motifs.triangle_count, motifs.edge_count) * 0.35
    )


def compute_bottleneck_score(motifs: StructuralMotifs) -> float:
    """Estimate bottleneck concentration."""
    total_parts = motifs.node_count + motifs.edge_count

    if total_parts == 0:
        return 0.0

    return clamp(motifs.bottleneck_count / total_parts)


def compute_persistence_score(stg: StructuralTruthGraph) -> float:
    """Estimate persistence from retained truth graph scores."""
    node_truth = [
        node.get("truth", {}).get("score", 0.0)
        for node in stg.nodes.values()
    ]
    edge_truth = [
        edge.get("truth", {}).get("score", 0.0)
        for edge in stg.edges.values()
    ]

    scores = node_truth + edge_truth

    if not scores:
        return 0.0

    return clamp(sum(scores) / len(scores))


def build_genome_sequence(
    *,
    motifs: StructuralMotifs,
    hierarchy_score: float,
    branching_score: float,
    cyclicity_score: float,
    bottleneck_score: float,
    persistence_score: float,
) -> tuple[str, ...]:
    """Build deterministic symbolic genome sequence from structural dominance."""
    components = [
        ("hub", len(motifs.hub_nodes)),
        ("bridge", len(motifs.bridge_edges)),
        ("articulation", len(motifs.articulation_nodes)),
        ("leaf", len(motifs.leaf_nodes)),
        ("chain", motifs.chain_count),
        ("triangle", motifs.triangle_count),
        ("star", motifs.star_count),
        ("bottleneck", motifs.bottleneck_count),
        ("cycle", motifs.cycle_like_count),
        ("hierarchy", hierarchy_score),
        ("branching", branching_score),
        ("cyclicity", cyclicity_score),
        ("persistence", persistence_score),
    ]

    ranked = sorted(
        components,
        key=lambda item: (
            item[1],
            item[0],
        ),
        reverse=True,
    )

    return tuple(
        name
        for name, value in ranked
        if value > 0
    )


def build_genome_summary(
    *,
    stg: StructuralTruthGraph,
    motifs: StructuralMotifs,
    hierarchy_score: float,
    branching_score: float,
    cyclicity_score: float,
    bottleneck_score: float,
    persistence_score: float,
    genome_sequence: tuple[str, ...],
) -> dict[str, Any]:
    """Build Structural Genome summary."""
    return {
        "version": GENOME_VERSION,
        "definition": (
            "Compact graph-native structural identity sequence derived from "
            "the Structural Truth Graph."
        ),
        "source": "StructuralTruthGraph",
        "stg_version": stg.version,
        "node_count": motifs.node_count,
        "edge_count": motifs.edge_count,
        "motif_richness": motifs.summary["motif_richness"],
        "hierarchy_score": hierarchy_score,
        "branching_score": branching_score,
        "cyclicity_score": cyclicity_score,
        "bottleneck_score": bottleneck_score,
        "persistence_score": persistence_score,
        "dominant_motif": genome_sequence[0] if genome_sequence else None,
        "genome_sequence": list(genome_sequence),
    }


def structural_genome_to_dict(
    genome: StructuralGenome,
) -> dict[str, Any]:
    """Convert Structural Genome to JSON-safe dictionary."""
    return asdict(genome)


def ratio(numerator: float, denominator: float) -> float:
    """Return safe ratio."""
    if denominator == 0:
        return 0.0

    return float(numerator) / float(denominator)


def clamp(value: float) -> float:
    """Clamp to 0-1."""
    return max(0.0, min(1.0, float(value)))