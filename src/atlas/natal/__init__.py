"""Motif engine public API."""

from atlas.motifs.catalog import MotifCounts
from atlas.motifs.detector import (
    count_bridge_edges,
    count_chain_nodes,
    count_dead_ends,
    count_hubs,
    count_isolated_nodes,
    count_reciprocal_pairs,
    count_self_loops,
    detect_motifs,
)
from atlas.motifs.identity import (
    build_edge_motif,
    build_identity_motif_summary,
    build_node_motif,
    detect_articulation_motifs,
    detect_bridge_motifs,
    detect_chain_motifs,
    detect_hub_motifs,
    detect_identity_graph_motifs,
    detect_leaf_motifs,
    detect_reciprocal_edge_motifs,
)
from atlas.motifs.statistics import dominant_motif, motif_density, total_motifs

__all__ = [
    "MotifCounts",
    "detect_motifs",
    "count_chain_nodes",
    "count_hubs",
    "count_self_loops",
    "count_bridge_edges",
    "count_dead_ends",
    "count_reciprocal_pairs",
    "count_isolated_nodes",
    "total_motifs",
    "motif_density",
    "dominant_motif",
    "detect_identity_graph_motifs",
    "detect_chain_motifs",
    "detect_hub_motifs",
    "detect_leaf_motifs",
    "detect_bridge_motifs",
    "detect_articulation_motifs",
    "detect_reciprocal_edge_motifs",
    "build_node_motif",
    "build_edge_motif",
    "build_identity_motif_summary",
]
