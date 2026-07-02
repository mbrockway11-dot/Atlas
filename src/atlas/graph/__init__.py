"""Atlas graph public API."""

from atlas.graph.analysis import (
    analyze_identity_graph,
    build_directed_adjacency,
    build_undirected_adjacency,
    connected_components,
)

from atlas.graph.identity_graph import (
    build_identity_graph_v2,
)

from atlas.graph.coherence import (
    classify_coherence,
    compute_coherence_field,
    compute_edge_coherence,
    compute_node_coherence,
)

from atlas.graph.reduction import (
    MAX_REDUCTION_ITERATIONS,
    reduce_identity_graph,
)

from atlas.graph.stack_audit import (
    STACK_AUDIT_VERSION,
    StackAudit,
    StackAuditIssue,
    audit_identity_stack,
    stack_audit_to_dict,
)

__all__ = [
    "analyze_identity_graph",
    "build_directed_adjacency",
    "build_undirected_adjacency",
    "connected_components",
    "build_identity_graph_v2",
    "classify_coherence",
    "compute_coherence_field",
    "compute_edge_coherence",
    "compute_node_coherence",
    "MAX_REDUCTION_ITERATIONS",
    "reduce_identity_graph",
    "STACK_AUDIT_VERSION",
    "StackAudit",
    "StackAuditIssue",
    "audit_identity_stack",
    "stack_audit_to_dict",
    "ATLAS_GRAPH_VERSION",
    "AtlasEdge",
    "AtlasGraph",
    "AtlasNode",
    "TEMPORAL_GRAPH_BRIDGE_VERSION",
    "build_temporal_graph",
    "GRAPH_METRICS_VERSION",
    "GraphMetrics",
    "compute_graph_metrics",
    "GRAPH_ACTIVATION_VERSION",
    "ActivatedEdge",
    "ActivatedNode",
    "GraphActivation",
    "build_graph_activation",
]

from atlas.graph.semantic import (
    ATLAS_GRAPH_VERSION,
    AtlasEdge,
    AtlasGraph,
    AtlasNode,
)


from atlas.graph.temporal_bridge import (
    TEMPORAL_GRAPH_BRIDGE_VERSION,
    build_temporal_graph,
)


from atlas.graph.metrics import (
    GRAPH_METRICS_VERSION,
    GraphMetrics,
    compute_graph_metrics,
)


from atlas.graph.activation import (
    GRAPH_ACTIVATION_VERSION,
    ActivatedEdge,
    ActivatedNode,
    GraphActivation,
    build_graph_activation,
)
