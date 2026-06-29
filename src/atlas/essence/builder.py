"""Essence graph builder."""

from atlas.ciphers import run_all_ciphers
from atlas.kamea.projection import project_values_to_kamea
from atlas.topology.graph import Edge, Node, TopologyGraph
from atlas.topology.graph_builder import build_graph_from_kamea_path


KAMEA_NAMES = [
    "saturn",
    "jupiter",
    "mars",
    "sun",
    "venus",
    "mercury",
    "moon",
]


def build_essence_graph(name: str) -> TopologyGraph:
    """Build one merged essence graph from all 21 profile graphs."""
    cipher_results = run_all_ciphers(name)

    all_nodes: list[Node] = []
    all_edges: list[Edge] = []
    node_weights: dict[Node, int] = {}
    edge_weights: dict[Edge, int] = {}

    for cipher_name, values in cipher_results.items():
        for kamea_name in KAMEA_NAMES:
            path = project_values_to_kamea(values, kamea_name)
            graph = build_graph_from_kamea_path(path)

            for node in graph.nodes:
                if node not in node_weights:
                    all_nodes.append(node)
                    node_weights[node] = 0

                node_weights[node] += graph.node_weights.get(node, 0)

            for edge in graph.edges:
                if edge not in edge_weights:
                    all_edges.append(edge)
                    edge_weights[edge] = 0

                edge_weights[edge] += graph.edge_weights.get(edge, 0)

    return TopologyGraph(
        nodes=tuple(all_nodes),
        edges=tuple(all_edges),
        node_weights=node_weights,
        edge_weights=edge_weights,
    )