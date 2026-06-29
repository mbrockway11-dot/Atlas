"""Build topology graphs from projected paths."""

from atlas.kamea.path import KameaPath
from atlas.topology.graph import Edge, Node, TopologyGraph


def build_graph_from_kamea_path(path: KameaPath) -> TopologyGraph:
    """Build a directed weighted graph from a Kamea path.

    Repeated coordinates become stronger node weights.
    Repeated directed edges become stronger edge weights.
    Only active path nodes and edges are included.
    """
    nodes = tuple(dict.fromkeys(path.coordinates))
    edges = tuple(dict.fromkeys(path.edges))

    node_weights: dict[Node, int] = path.node_counts
    edge_weights: dict[Edge, int] = path.edge_counts

    return TopologyGraph(
        nodes=nodes,
        edges=edges,
        node_weights=node_weights,
        edge_weights=edge_weights,
    )