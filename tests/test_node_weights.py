from atlas.kamea.path import KameaPath
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


def test_node_weight_utilities():
    path = KameaPath(
        raw_values=(1, 5, 10, 5),
        reduced_values=(1, 5, 1, 5),
        coordinates=((2, 1), (1, 1), (2, 1), (1, 1)),
    )

    graph = build_graph_from_kamea_path(path)

    assert get_node_weight(graph, (2, 1)) == 2
    assert get_node_weight(graph, (1, 1)) == 2
    assert get_node_weight(graph, (0, 0)) == 0

    assert node_depth(graph, (2, 1)) == 2
    assert max_node_weight(graph) == 2

    assert repeated_nodes(graph) == {
        (2, 1): 2,
        (1, 1): 2,
    }


def test_edge_weight_utilities():
    path = KameaPath(
        raw_values=(1, 5, 10, 5),
        reduced_values=(1, 5, 1, 5),
        coordinates=((2, 1), (1, 1), (2, 1), (1, 1)),
    )

    graph = build_graph_from_kamea_path(path)

    edge_a = ((2, 1), (1, 1))
    edge_b = ((1, 1), (2, 1))
    missing_edge = ((0, 0), (1, 1))

    assert get_edge_weight(graph, edge_a) == 2
    assert get_edge_weight(graph, edge_b) == 1
    assert get_edge_weight(graph, missing_edge) == 0

    assert edge_reinforcement(graph, edge_a) == 2
    assert max_edge_weight(graph) == 2

    assert repeated_edges(graph) == {
        edge_a: 2,
    }


def test_normalized_weights():
    path = KameaPath(
        raw_values=(1, 5, 10, 5),
        reduced_values=(1, 5, 1, 5),
        coordinates=((2, 1), (1, 1), (2, 1), (1, 1)),
    )

    graph = build_graph_from_kamea_path(path)

    node_weights = normalized_node_weights(graph)
    edge_weights = normalized_edge_weights(graph)

    assert node_weights[(2, 1)] == 1.0
    assert node_weights[(1, 1)] == 1.0

    assert edge_weights[((2, 1), (1, 1))] == 1.0
    assert edge_weights[((1, 1), (2, 1))] == 0.5