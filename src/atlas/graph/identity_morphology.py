"""Identity Morphology Engine.

The Identity Morphology Engine compares two graph-native identity stacks and
describes the structural transformations between them.

It does not interpret personality. It measures graph transformation:
shared structure, added structure, removed structure, motif mutation,
genome mutation, topology mutation, and resonance mutation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from atlas.graph.identity_stack import IdentityGraphStack


MORPHOLOGY_VERSION = "1.0"


@dataclass(frozen=True)
class IdentityMorphology:
    """Structural transformation comparison between two identity stacks."""

    version: str
    name_a: str
    name_b: str
    node_overlap: float
    edge_overlap: float
    shared_node_count: int
    shared_edge_count: int
    added_node_count: int
    removed_node_count: int
    added_edge_count: int
    removed_edge_count: int
    motif_mutation: dict[str, float]
    genome_mutation: dict[str, Any]
    topology_mutation: dict[str, Any]
    resonance_mutation: dict[str, Any]
    structural_edit_distance: float
    morphology_class: str
    summary: dict[str, Any]


def compare_identity_morphology(
    stack_a: IdentityGraphStack,
    stack_b: IdentityGraphStack,
) -> IdentityMorphology:
    """Compare two identity stacks as structural morphologies."""
    nodes_a = set(stack_a.stg.nodes)
    nodes_b = set(stack_b.stg.nodes)

    edges_a = set(stack_a.stg.edges)
    edges_b = set(stack_b.stg.edges)

    shared_nodes = nodes_a & nodes_b
    shared_edges = edges_a & edges_b

    added_nodes = nodes_b - nodes_a
    removed_nodes = nodes_a - nodes_b

    added_edges = edges_b - edges_a
    removed_edges = edges_a - edges_b

    node_overlap = jaccard(nodes_a, nodes_b)
    edge_overlap = jaccard(edges_a, edges_b)

    motif_mutation = compare_motif_mutation(stack_a, stack_b)
    genome_mutation = compare_genome_mutation(stack_a, stack_b)
    topology_mutation = compare_topology_mutation(stack_a, stack_b)
    resonance_mutation = compare_resonance_mutation(stack_a, stack_b)

    structural_edit_distance = compute_structural_edit_distance(
        node_overlap=node_overlap,
        edge_overlap=edge_overlap,
        motif_mutation_score=motif_mutation["mutation_score"],
        topology_mutation_score=topology_mutation["mutation_score"],
        resonance_mutation_score=resonance_mutation["mutation_score"],
    )

    morphology_class = classify_morphology(structural_edit_distance)

    summary = {
        "version": MORPHOLOGY_VERSION,
        "definition": (
            "Structural transformation comparison between two graph-native "
            "IdentityGraphStack objects."
        ),
        "name_a": stack_a.name,
        "name_b": stack_b.name,
        "node_overlap": node_overlap,
        "edge_overlap": edge_overlap,
        "shared_node_count": len(shared_nodes),
        "shared_edge_count": len(shared_edges),
        "added_node_count": len(added_nodes),
        "removed_node_count": len(removed_nodes),
        "added_edge_count": len(added_edges),
        "removed_edge_count": len(removed_edges),
        "structural_edit_distance": structural_edit_distance,
        "morphology_class": morphology_class,
    }

    return IdentityMorphology(
        version=MORPHOLOGY_VERSION,
        name_a=stack_a.name,
        name_b=stack_b.name,
        node_overlap=node_overlap,
        edge_overlap=edge_overlap,
        shared_node_count=len(shared_nodes),
        shared_edge_count=len(shared_edges),
        added_node_count=len(added_nodes),
        removed_node_count=len(removed_nodes),
        added_edge_count=len(added_edges),
        removed_edge_count=len(removed_edges),
        motif_mutation=motif_mutation,
        genome_mutation=genome_mutation,
        topology_mutation=topology_mutation,
        resonance_mutation=resonance_mutation,
        structural_edit_distance=structural_edit_distance,
        morphology_class=morphology_class,
        summary=summary,
    )


def compare_motif_mutation(
    stack_a: IdentityGraphStack,
    stack_b: IdentityGraphStack,
) -> dict[str, float]:
    """Compare motif-level mutation."""
    fields = [
        "chain_count",
        "triangle_count",
        "star_count",
        "bottleneck_count",
        "cycle_like_count",
    ]

    deltas = {
        field: abs(
            float(getattr(stack_a.motifs, field))
            - float(getattr(stack_b.motifs, field))
        )
        for field in fields
    }

    scale = max(
        sum(float(getattr(stack_a.motifs, field)) for field in fields),
        sum(float(getattr(stack_b.motifs, field)) for field in fields),
        1.0,
    )

    mutation_score = clamp(sum(deltas.values()) / scale)

    return {
        **deltas,
        "mutation_score": mutation_score,
    }


def compare_genome_mutation(
    stack_a: IdentityGraphStack,
    stack_b: IdentityGraphStack,
) -> dict[str, Any]:
    """Compare genome sequence and genome score mutation."""
    sequence_a = set(stack_a.genome.genome_sequence)
    sequence_b = set(stack_b.genome.genome_sequence)

    shared_sequence = sorted(sequence_a & sequence_b)
    added_sequence = sorted(sequence_b - sequence_a)
    removed_sequence = sorted(sequence_a - sequence_b)

    vector_fields = [
        "hierarchy_score",
        "branching_score",
        "cyclicity_score",
        "bottleneck_score",
        "persistence_score",
        "motif_richness",
    ]

    score_deltas = {
        field: abs(
            float(getattr(stack_a.genome, field))
            - float(getattr(stack_b.genome, field))
        )
        for field in vector_fields
    }

    mutation_score = clamp(
        (
            1.0 - jaccard(sequence_a, sequence_b)
            + mean(list(score_deltas.values()))
        )
        / 2.0
    )

    return {
        "shared_sequence": shared_sequence,
        "added_sequence": added_sequence,
        "removed_sequence": removed_sequence,
        "score_deltas": score_deltas,
        "mutation_score": mutation_score,
    }


def compare_topology_mutation(
    stack_a: IdentityGraphStack,
    stack_b: IdentityGraphStack,
) -> dict[str, Any]:
    """Compare topology behavior mutation."""
    vector_a = stack_a.topology.topology_vector
    vector_b = stack_b.topology.topology_vector

    shared_keys = sorted(set(vector_a) & set(vector_b))

    deltas = {
        key: abs(float(vector_a[key]) - float(vector_b[key]))
        for key in shared_keys
    }

    class_changed = stack_a.topology.topology_class != stack_b.topology.topology_class
    flow_changed = stack_a.topology.flow_pattern != stack_b.topology.flow_pattern
    organization_changed = (
        stack_a.topology.organization_pattern
        != stack_b.topology.organization_pattern
    )
    stability_changed = (
        stack_a.topology.stability_pattern
        != stack_b.topology.stability_pattern
    )

    categorical_penalty = mean(
        [
            1.0 if class_changed else 0.0,
            1.0 if flow_changed else 0.0,
            1.0 if organization_changed else 0.0,
            1.0 if stability_changed else 0.0,
        ]
    )

    mutation_score = clamp(
        (mean(list(deltas.values())) + categorical_penalty) / 2.0
    )

    return {
        "from_class": stack_a.topology.topology_class,
        "to_class": stack_b.topology.topology_class,
        "from_flow": stack_a.topology.flow_pattern,
        "to_flow": stack_b.topology.flow_pattern,
        "from_organization": stack_a.topology.organization_pattern,
        "to_organization": stack_b.topology.organization_pattern,
        "from_stability": stack_a.topology.stability_pattern,
        "to_stability": stack_b.topology.stability_pattern,
        "score_deltas": deltas,
        "categorical_penalty": categorical_penalty,
        "mutation_score": mutation_score,
    }


def compare_resonance_mutation(
    stack_a: IdentityGraphStack,
    stack_b: IdentityGraphStack,
) -> dict[str, Any]:
    """Compare resonance behavior mutation."""
    vector_a = stack_a.resonance.resonance_vector
    vector_b = stack_b.resonance.resonance_vector

    shared_keys = sorted(set(vector_a) & set(vector_b))

    deltas = {
        key: abs(float(vector_a[key]) - float(vector_b[key]))
        for key in shared_keys
    }

    class_changed = (
        stack_a.resonance.resonance_class
        != stack_b.resonance.resonance_class
    )
    activation_changed = (
        stack_a.resonance.activation_pattern
        != stack_b.resonance.activation_pattern
    )
    propagation_changed = (
        stack_a.resonance.propagation_pattern
        != stack_b.resonance.propagation_pattern
    )
    damping_changed = (
        stack_a.resonance.damping_pattern
        != stack_b.resonance.damping_pattern
    )

    categorical_penalty = mean(
        [
            1.0 if class_changed else 0.0,
            1.0 if activation_changed else 0.0,
            1.0 if propagation_changed else 0.0,
            1.0 if damping_changed else 0.0,
        ]
    )

    mutation_score = clamp(
        (mean(list(deltas.values())) + categorical_penalty) / 2.0
    )

    return {
        "from_class": stack_a.resonance.resonance_class,
        "to_class": stack_b.resonance.resonance_class,
        "from_activation": stack_a.resonance.activation_pattern,
        "to_activation": stack_b.resonance.activation_pattern,
        "from_propagation": stack_a.resonance.propagation_pattern,
        "to_propagation": stack_b.resonance.propagation_pattern,
        "from_damping": stack_a.resonance.damping_pattern,
        "to_damping": stack_b.resonance.damping_pattern,
        "score_deltas": deltas,
        "categorical_penalty": categorical_penalty,
        "mutation_score": mutation_score,
    }


def compute_structural_edit_distance(
    *,
    node_overlap: float,
    edge_overlap: float,
    motif_mutation_score: float,
    topology_mutation_score: float,
    resonance_mutation_score: float,
) -> float:
    """Compute bounded structural edit distance."""
    node_distance = 1.0 - node_overlap
    edge_distance = 1.0 - edge_overlap

    return clamp(
        node_distance * 0.25
        + edge_distance * 0.25
        + motif_mutation_score * 0.20
        + topology_mutation_score * 0.15
        + resonance_mutation_score * 0.15
    )


def classify_morphology(distance: float) -> str:
    """Classify structural edit distance.

    The Identity Morphology Engine measures graph transformation, not simple
    feature similarity. Thresholds are intentionally conservative so that
    moderate graph edits are surfaced instead of being hidden as minor.
    """
    distance = clamp(distance)

    if distance >= 0.80:
        return "structural_reconstruction"

    if distance >= 0.60:
        return "major_transformation"

    if distance >= 0.40:
        return "moderate_transformation"

    if distance >= 0.20:
        return "minor_transformation"

    if distance >= 0.05:
        return "local_variation"

    return "near_isomorphic"


def identity_morphology_to_dict(
    morphology: IdentityMorphology,
) -> dict[str, Any]:
    """Convert IdentityMorphology to JSON-safe dictionary."""
    return asdict(morphology)


def jaccard(a: set[str], b: set[str]) -> float:
    """Return Jaccard similarity."""
    if not a and not b:
        return 1.0

    union = a | b

    if not union:
        return 0.0

    return len(a & b) / len(union)


def mean(values: list[float]) -> float:
    """Return arithmetic mean."""
    if not values:
        return 0.0

    return sum(values) / len(values)


def clamp(value: float) -> float:
    """Clamp to 0-1."""
    return max(0.0, min(1.0, float(value)))