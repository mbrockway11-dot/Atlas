from atlas.features.metrics import (
    connected_components,
    edge_count,
    edge_density,
    graph_symmetry,
    in_degree,
    node_count,
    out_degree,
    repeated_edges,
    repeated_nodes,
    unique_edges,
    unique_nodes,
    weighted_in_degree,
    weighted_out_degree,
)
from atlas.topology.graph import TopologyGraph


def test_basic_graph_metrics():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2)),
        edges=(((0, 0), (1, 1)), ((1, 1), (2, 2))),
        node_weights={
            (0, 0): 1,
            (1, 1): 2,
            (2, 2): 1,
        },
        edge_weights={
            ((0, 0), (1, 1)): 3,
            ((1, 1), (2, 2)): 1,
        },
    )

    assert node_count(graph) == 3
    assert edge_count(graph) == 2
    assert unique_nodes(graph) == ((0, 0), (1, 1), (2, 2))
    assert unique_edges(graph) == (((0, 0), (1, 1)), ((1, 1), (2, 2)))


def test_repeated_node_and_edge_metrics():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={
            (0, 0): 1,
            (1, 1): 3,
        },
        edge_weights={
            ((0, 0), (1, 1)): 2,
        },
    )

    assert repeated_nodes(graph) == {(1, 1): 3}
    assert repeated_edges(graph) == {((0, 0), (1, 1)): 2}


def test_edge_density():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2)),
        edges=(((0, 0), (1, 1)), ((1, 1), (2, 2))),
        node_weights={(0, 0): 1, (1, 1): 1, (2, 2): 1},
        edge_weights={((0, 0), (1, 1)): 1, ((1, 1), (2, 2)): 1},
    )

    assert edge_density(graph) == 2 / 6


def test_degree_metrics():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2)),
        edges=(((0, 0), (1, 1)), ((1, 1), (2, 2)), ((0, 0), (2, 2))),
        node_weights={(0, 0): 1, (1, 1): 1, (2, 2): 1},
        edge_weights={
            ((0, 0), (1, 1)): 2,
            ((1, 1), (2, 2)): 3,
            ((0, 0), (2, 2)): 5,
        },
    )

    assert in_degree(graph) == {
        (0, 0): 0,
        (1, 1): 1,
        (2, 2): 2,
    }

    assert out_degree(graph) == {
        (0, 0): 2,
        (1, 1): 1,
        (2, 2): 0,
    }

    assert weighted_in_degree(graph) == {
        (0, 0): 0,
        (1, 1): 2,
        (2, 2): 8,
    }

    assert weighted_out_degree(graph) == {
        (0, 0): 7,
        (1, 1): 3,
        (2, 2): 0,
    }


def test_connected_components():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1), (8, 8), (9, 9)),
        edges=(((0, 0), (1, 1)), ((8, 8), (9, 9))),
        node_weights={(0, 0): 1, (1, 1): 1, (8, 8): 1, (9, 9): 1},
        edge_weights={((0, 0), (1, 1)): 1, ((8, 8), (9, 9)): 1},
    )

    assert connected_components(graph) == (
        ((0, 0), (1, 1)),
        ((8, 8), (9, 9)),
    )


def test_graph_symmetry():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2)),
        edges=(
            ((0, 0), (1, 1)),
            ((1, 1), (0, 0)),
            ((1, 1), (2, 2)),
        ),
        node_weights={(0, 0): 1, (1, 1): 1, (2, 2): 1},
        edge_weights={
            ((0, 0), (1, 1)): 1,
            ((1, 1), (0, 0)): 1,
            ((1, 1), (2, 2)): 1,
        },
    )

    assert graph_symmetry(graph) == 2 / 3