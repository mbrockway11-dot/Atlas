from atlas.kamea.path import KameaPath
from atlas.topology.graph_builder import build_graph_from_kamea_path


def test_build_graph_from_kamea_path():
    path = KameaPath(
        raw_values=(1, 5, 10),
        reduced_values=(1, 5, 1),
        coordinates=((2, 1), (1, 1), (2, 1)),
    )

    graph = build_graph_from_kamea_path(path)

    assert graph.node_count == 2
    assert graph.edge_count == 2

    assert graph.node_weights[(2, 1)] == 2
    assert graph.node_weights[(1, 1)] == 1

    assert graph.edge_weights[((2, 1), (1, 1))] == 1
    assert graph.edge_weights[((1, 1), (2, 1))] == 1


def test_graph_incoming_and_outgoing_edges():
    path = KameaPath(
        raw_values=(1, 5, 10, 5),
        reduced_values=(1, 5, 1, 5),
        coordinates=((2, 1), (1, 1), (2, 1), (1, 1)),
    )

    graph = build_graph_from_kamea_path(path)

    assert graph.node_count == 2
    assert graph.edge_count == 2

    assert graph.edge_weights[((2, 1), (1, 1))] == 2
    assert graph.edge_weights[((1, 1), (2, 1))] == 1

    assert graph.outgoing_edges((2, 1)) == (((2, 1), (1, 1)),)
    assert graph.incoming_edges((2, 1)) == (((1, 1), (2, 1)),)