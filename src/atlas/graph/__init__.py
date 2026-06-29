"""Atlas graph public API."""

from atlas.graph.analysis import (
    analyze_identity_graph,
    build_undirected_adjacency,
)

from atlas.graph.attractor import (
    extract_structural_attractor,
)

from atlas.graph.coherence import (
    build_coherence_summary,
    clamp,
    classify_coherence,
    compute_coherence_field,
    compute_edge_coherence,
    compute_node_coherence,
    count_region,
    normalized,
    top_by_coherence,
)

from atlas.graph.identity_graph import (
    apply_construction_pass,
    apply_edge_visit,
    apply_node_visit,
    build_identity_graph_summary,
    build_identity_graph_v2,
    empty_identity_graph,
    finalize_identity_graph,
    most_common_coordinate,
    top_records,
)

from atlas.graph.reduction import (
    MAX_REDUCTION_ITERATIONS,
    build_reduced_summary,
    copy_record,
    find_removable_leaf_noise,
    graph_copy,
    is_removable_leaf_noise,
    reduce_identity_graph,
    remove_nodes,
)

__all__ = [
    # Identity graph
    "build_identity_graph_v2",
    "empty_identity_graph",
    "apply_construction_pass",
    "apply_node_visit",
    "apply_edge_visit",
    "finalize_identity_graph",
    "most_common_coordinate",
    "build_identity_graph_summary",
    "top_records",

    # Analysis
    "analyze_identity_graph",
    "build_undirected_adjacency",

    # Coherence
    "compute_coherence_field",
    "compute_node_coherence",
    "compute_edge_coherence",
    "build_coherence_summary",
    "count_region",
    "top_by_coherence",
    "classify_coherence",
    "normalized",
    "clamp",

    # Reduction
    "MAX_REDUCTION_ITERATIONS",
    "reduce_identity_graph",
    "find_removable_leaf_noise",
    "is_removable_leaf_noise",
    "remove_nodes",
    "build_reduced_summary",
    "graph_copy",
    "copy_record",

    # Structural attractor
    "extract_structural_attractor",
]