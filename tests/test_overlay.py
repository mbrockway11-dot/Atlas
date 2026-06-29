from atlas.topology.graph import TopologyGraph
from atlas.topology.overlay import (
    overlay_graphs,
    overlay_pair,
    shared_edges,
    shared_nodes,
    unique_edges,
    unique_nodes,
)


def test_overlay_graphs_sums_shared_weights():
    graph_a = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={
            (0, 0): 1,
            (1, 1): 2,
        },
        edge_weights={
            ((0, 0), (1, 1)): 3,
        },
    )

    graph_b = TopologyGraph(
        nodes=((1, 1), (2, 2)),
        edges=(((1, 1), (2, 2)), ((0, 0), (1, 1))),
        node_weights={
            (1, 1): 4,
            (2, 2): 5,
        },
        edge_weights={
            ((1, 1), (2, 2)): 6,
            ((0, 0), (1, 1)): 7,
        },
    )

    overlay = overlay_graphs([graph_a, graph_b])

    assert overlay.nodes == ((0, 0), (1, 1), (2, 2))
    assert overlay.edges == (
        ((0, 0), (1, 1)),
        ((1, 1), (2, 2)),
    )

    assert overlay.node_weights[(0, 0)] == 1
    assert overlay.node_weights[(1, 1)] == 6
    assert overlay.node_weights[(2, 2)] == 5

    assert overlay.edge_weights[((0, 0), (1, 1))] == 10
    assert overlay.edge_weights[((1, 1), (2, 2))] == 6


def test_overlay_pair():
    graph_a = TopologyGraph(
        nodes=((0, 0),),
        edges=(),
        node_weights={(0, 0): 1},
        edge_weights={},
    )

    graph_b = TopologyGraph(
        nodes=((0, 0),),
        edges=(),
        node_weights={(0, 0): 2},
        edge_weights={},
    )

    overlay = overlay_pair(graph_a, graph_b)

    assert overlay.nodes == ((0, 0),)
    assert overlay.node_weights[(0, 0)] == 3


def test_shared_and_unique_nodes():
    graph_a = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2)),
        edges=(),
        node_weights={(0, 0): 1, (1, 1): 1, (2, 2): 1},
        edge_weights={},
    )

    graph_b = TopologyGraph(
        nodes=((1, 1), (2, 2), (3, 3)),
        edges=(),
        node_weights={(1, 1): 1, (2, 2): 1, (3, 3): 1},
        edge_weights={},
    )

    assert shared_nodes(graph_a, graph_b) == ((1, 1), (2, 2))
    assert unique_nodes(graph_a, graph_b) == ((0, 0),)


def test_shared_and_unique_edges():
    edge_a = ((0, 0), (1, 1))
    edge_b = ((1, 1), (2, 2))
    edge_c = ((2, 2), (3, 3))

    graph_a = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2)),
        edges=(edge_a, edge_b),
        node_weights={(0, 0): 1, (1, 1): 1, (2, 2): 1},
        edge_weights={edge_a: 1, edge_b: 1},
    )

    graph_b = TopologyGraph(
        nodes=((1, 1), (2, 2), (3, 3)),
        edges=(edge_b, edge_c),
        node_weights={(1, 1): 1, (2, 2): 1, (3, 3): 1},
        edge_weights={edge_b: 1, edge_c: 1},
    )

    assert shared_edges(graph_a, graph_b) == (edge_b,)
    assert unique_edges(graph_a, graph_b) == (edge_a,)