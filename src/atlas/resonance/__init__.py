"""Resonance engine public API."""

from atlas.resonance.alignment import (
    directional_alignment,
    hub_alignment,
    motif_alignment,
    pattern_alignment,
    structural_alignment,
)
from atlas.resonance.clustering import GraphCluster, cluster_by_resonance
from atlas.resonance.field import (
    ADAPTIVE_THRESHOLD,
    CORE_THRESHOLD,
    build_resonance_field,
    build_resonance_summary,
    classify_field_region,
    enrich_resonance_record,
    top_resonant,
)
from atlas.resonance.resonance import ResonanceResult, calculate_resonance
from atlas.resonance.similarity import (
    edge_jaccard_similarity,
    edge_weight_similarity,
    node_jaccard_similarity,
    node_weight_similarity,
    topology_vector_similarity,
)
from atlas.resonance.vector import (
    TopologyVector,
    build_topology_vector,
    vector_to_tuple,
)

__all__ = [
    "TopologyVector",
    "build_topology_vector",
    "vector_to_tuple",
    "node_jaccard_similarity",
    "edge_jaccard_similarity",
    "node_weight_similarity",
    "edge_weight_similarity",
    "topology_vector_similarity",
    "hub_alignment",
    "pattern_alignment",
    "motif_alignment",
    "directional_alignment",
    "structural_alignment",
    "ResonanceResult",
    "calculate_resonance",
    "GraphCluster",
    "cluster_by_resonance",
    "CORE_THRESHOLD",
    "ADAPTIVE_THRESHOLD",
    "build_resonance_field",
    "build_resonance_summary",
    "classify_field_region",
    "enrich_resonance_record",
    "top_resonant",
]