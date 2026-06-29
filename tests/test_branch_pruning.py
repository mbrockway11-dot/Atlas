from atlas.topology.branch_pruning import (
    prune_edges_below_weight,
    prune_graph,
    prune_isolated_nodes,
)
from atlas.topology.graph import TopologyGraph


def test_prune_graph_by_node_weight():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2)),
        edges=(((0, 0), (1, 1)), ((1, 1), (2, 2))),
        node_weights={
            (0, 0): 1,
            (1, 1): 2,
            (2, 2): 1,
        },
        edge_weights={
            ((0, 0), (1, 1)): 1,
            ((1, 1), (2, 2)): 1,
        },
    )

    pruned = prune_graph(graph, min_node_weight=2)

    assert pruned.nodes == ((1, 1),)
    assert pruned.edges == ()
    assert pruned.node_weights == {(1, 1): 2}
    assert pruned.edge_weights == {}


def test_prune_graph_by_edge_weight():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2)),
        edges=(((0, 0), (1, 1)), ((1, 1), (2, 2))),
        node_weights={
            (0, 0): 1,
            (1, 1): 2,
            (2, 2): 1,
        },
        edge_weights={
            ((0, 0), (1, 1)): 2,
            ((1, 1), (2, 2)): 1,
        },
    )

    pruned = prune_graph(graph, min_edge_weight=2)

    assert pruned.nodes == ((0, 0), (1, 1), (2, 2))
    assert pruned.edges == (((0, 0), (1, 1)),)
    assert pruned.edge_weights == {((0, 0), (1, 1)): 2}


def test_prune_isolated_nodes():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2)),
        edges=(((0, 0), (1, 1)),),
        node_weights={
            (0, 0): 1,
            (1, 1): 1,
            (2, 2): 3,
        },
        edge_weights={
            ((0, 0), (1, 1)): 1,
        },
    )

    pruned = prune_isolated_nodes(graph)

    assert pruned.nodes == ((0, 0), (1, 1))
    assert pruned.edges == (((0, 0), (1, 1)),)
    assert (2, 2) not in pruned.node_weights


def test_prune_edges_below_weight():
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

    pruned = prune_edges_below_weight(graph, min_edge_weight=2)

    assert pruned.nodes == ((0, 0), (1, 1))
    assert pruned.edges == (((0, 0), (1, 1)),)
    assert pruned.edge_weights == {((0, 0), (1, 1)): 3}