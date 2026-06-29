from atlas.topology.graph import TopologyGraph
from atlas.topology.structural_similarity import compare_structural_similarity


def test_identical_graphs_have_full_structural_similarity():
    graph = TopologyGraph(
        nodes=((0, 0), (0, 1)),
        edges=(((0, 0), (0, 1)),),
        node_weights={(0, 0): 1, (0, 1): 2},
        edge_weights={((0, 0), (0, 1)): 1},
    )

    result = compare_structural_similarity(graph, graph)

    assert result.node_overlap == 1.0
    assert result.edge_overlap == 1.0
    assert result.node_weight_similarity == 1.0
    assert result.edge_weight_similarity == 1.0
    assert result.structural_similarity == 1.0


def test_different_graphs_have_partial_similarity():
    graph_a = TopologyGraph(
        nodes=((0, 0), (0, 1)),
        edges=(((0, 0), (0, 1)),),
        node_weights={(0, 0): 1, (0, 1): 2},
        edge_weights={((0, 0), (0, 1)): 1},
    )

    graph_b = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 1, (1, 1): 3},
        edge_weights={((0, 0), (1, 1)): 1},
    )

    result = compare_structural_similarity(graph_a, graph_b)

    assert result.node_overlap == 1 / 3
    assert result.edge_overlap == 0.0
    assert 0.0 <= result.structural_similarity <= 1.0
    assert result.strongest_shared_nodes == ((0, 0),)


def test_weight_similarity_detects_weight_drift():
    graph_a = TopologyGraph(
        nodes=((0, 0),),
        edges=(),
        node_weights={(0, 0): 1},
        edge_weights={},
    )

    graph_b = TopologyGraph(
        nodes=((0, 0),),
        edges=(),
        node_weights={(0, 0): 3},
        edge_weights={},
    )

    result = compare_structural_similarity(graph_a, graph_b)

    assert result.node_overlap == 1.0
    assert result.node_weight_similarity == 1 - (2 / 3)
    assert result.strongest_node_deltas == {(0, 0): -2}