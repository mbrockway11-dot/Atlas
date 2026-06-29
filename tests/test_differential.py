from atlas.topology.differential import compare_graphs
from atlas.topology.graph import TopologyGraph


def test_compare_graphs_shared_and_unique_structure():
    edge_a = ((0, 0), (1, 1))
    edge_b = ((1, 1), (2, 2))
    edge_c = ((2, 2), (3, 3))

    graph_a = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2)),
        edges=(edge_a, edge_b),
        node_weights={
            (0, 0): 1,
            (1, 1): 3,
            (2, 2): 5,
        },
        edge_weights={
            edge_a: 2,
            edge_b: 4,
        },
    )

    graph_b = TopologyGraph(
        nodes=((1, 1), (2, 2), (3, 3)),
        edges=(edge_b, edge_c),
        node_weights={
            (1, 1): 2,
            (2, 2): 8,
            (3, 3): 13,
        },
        edge_weights={
            edge_b: 1,
            edge_c: 7,
        },
    )

    diff = compare_graphs(graph_a, graph_b)

    assert diff.shared_nodes == ((1, 1), (2, 2))
    assert diff.shared_edges == (edge_b,)

    assert diff.unique_nodes_a == ((0, 0),)
    assert diff.unique_nodes_b == ((3, 3),)

    assert diff.unique_edges_a == (edge_a,)
    assert diff.unique_edges_b == (edge_c,)

    assert diff.node_weight_delta[(0, 0)] == 1
    assert diff.node_weight_delta[(1, 1)] == 1
    assert diff.node_weight_delta[(2, 2)] == -3
    assert diff.node_weight_delta[(3, 3)] == -13

    assert diff.edge_weight_delta[edge_a] == 2
    assert diff.edge_weight_delta[edge_b] == 3
    assert diff.edge_weight_delta[edge_c] == -7


def test_compare_graphs_overlap_ratios():
    graph_a = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={((0, 0), (1, 1)): 1},
    )

    graph_b = TopologyGraph(
        nodes=((1, 1), (2, 2)),
        edges=(((1, 1), (2, 2)),),
        node_weights={(1, 1): 1, (2, 2): 1},
        edge_weights={((1, 1), (2, 2)): 1},
    )

    diff = compare_graphs(graph_a, graph_b)

    assert diff.node_overlap_ratio == 1 / 3
    assert diff.edge_overlap_ratio == 0.0


def test_compare_empty_graphs():
    graph_a = TopologyGraph(
        nodes=(),
        edges=(),
        node_weights={},
        edge_weights={},
    )

    graph_b = TopologyGraph(
        nodes=(),
        edges=(),
        node_weights={},
        edge_weights={},
    )

    diff = compare_graphs(graph_a, graph_b)

    assert diff.shared_nodes == ()
    assert diff.shared_edges == ()
    assert diff.node_overlap_ratio == 0.0
    assert diff.edge_overlap_ratio == 0.0