"""Topology engine public API."""

from atlas.topology.branch_pruning import (
    prune_edges_below_weight,
    prune_graph,
    prune_isolated_nodes,
)
from atlas.topology.differential import GraphDifferential, compare_graphs
from atlas.topology.graph import Edge, Node, TopologyGraph
from atlas.topology.graph_builder import build_graph_from_kamea_path
from atlas.topology.node_weights import (
    edge_reinforcement,
    get_edge_weight,
    get_node_weight,
    max_edge_weight,
    max_node_weight,
    node_depth,
    normalized_edge_weights,
    normalized_node_weights,
    repeated_edges,
    repeated_nodes,
)
from atlas.topology.overlay import (
    overlay_graphs,
    overlay_pair,
    shared_edges,
    shared_nodes,
    unique_edges,
    unique_nodes,
)

__all__ = [
    "Node",
    "Edge",
    "TopologyGraph",
    "build_graph_from_kamea_path",
    "get_node_weight",
    "get_edge_weight",
    "repeated_nodes",
    "repeated_edges",
    "node_depth",
    "edge_reinforcement",
    "max_node_weight",
    "max_edge_weight",
    "normalized_node_weights",
    "normalized_edge_weights",
    "prune_graph",
    "prune_isolated_nodes",
    "prune_edges_below_weight",
    "overlay_graphs",
    "overlay_pair",
    "shared_nodes",
    "shared_edges",
    "unique_nodes",
    "unique_edges",
    "GraphDifferential",
    "compare_graphs",
]