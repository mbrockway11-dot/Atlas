"""Atlas identity topology graph API."""

from atlas.identity.builder import (
    build_identity_graph,
    build_identity_graph_summary,
    build_identity_layers,
    build_layer_similarity_edges,
)
from atlas.identity.layer import IdentityLayer, identity_layer_to_dict
from atlas.identity.persistence import (
    DEFAULT_PERSISTENCE_THRESHOLD,
    build_identity_persistence,
    build_node_trajectory_metrics,
    build_persistence_summary,
    collect_edge_records,
    collect_node_records,
    enrich_persistence_record,
    split_by_persistence,
)
from atlas.identity.similarity import (
    compare_identity_layers,
    layer_feature_vector,
    layer_subtype_vector,
)

__all__ = [
    "IdentityLayer",
    "identity_layer_to_dict",
    "build_identity_layers",
    "build_identity_graph",
    "build_layer_similarity_edges",
    "build_identity_graph_summary",
    "layer_subtype_vector",
    "layer_feature_vector",
    "compare_identity_layers",
    "DEFAULT_PERSISTENCE_THRESHOLD",
    "build_identity_persistence",
    "collect_node_records",
    "collect_edge_records",
    "split_by_persistence",
    "enrich_persistence_record",
    "build_node_trajectory_metrics",
    "build_persistence_summary",
]