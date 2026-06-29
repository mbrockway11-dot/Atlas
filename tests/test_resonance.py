from atlas.resonance.alignment import structural_alignment
from atlas.resonance.clustering import cluster_by_resonance
from atlas.resonance.resonance import calculate_resonance
from atlas.resonance.similarity import (
    edge_jaccard_similarity,
    edge_weight_similarity,
    node_jaccard_similarity,
    node_weight_similarity,
    topology_vector_similarity,
)
from atlas.resonance.vector import build_topology_vector, vector_to_tuple
from atlas.topology.graph import TopologyGraph


def test_jaccard_similarity():
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

    assert node_jaccard_similarity(graph_a, graph_b) == 1 / 3
    assert edge_jaccard_similarity(graph_a, graph_b) == 0.0


def test_weight_similarity():
    graph_a = TopologyGraph(
        nodes=((0, 0),),
        edges=(),
        node_weights={(0, 0): 2},
        edge_weights={},
    )

    graph_b = TopologyGraph(
        nodes=((0, 0),),
        edges=(),
        node_weights={(0, 0): 4},
        edge_weights={},
    )

    assert node_weight_similarity(graph_a, graph_b) == 0.5
    assert edge_weight_similarity(graph_a, graph_b) == 1.0


def test_topology_vector():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={((0, 0), (1, 1)): 1},
    )

    vector = build_topology_vector(graph)

    assert len(vector_to_tuple(vector)) == 14


def test_topology_vector_similarity_identical_graphs():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={((0, 0), (1, 1)): 1},
    )

    assert topology_vector_similarity(graph, graph) == 1.0


def test_structural_alignment_identical_graphs():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={((0, 0), (1, 1)): 1},
    )

    assert structural_alignment(graph, graph) == 1.0


def test_calculate_resonance_identical_graphs():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={((0, 0), (1, 1)): 1},
    )

    resonance = calculate_resonance(graph, graph)

    assert resonance.overall == 1.0
    assert resonance.node_similarity == 1.0
    assert resonance.edge_similarity == 1.0
    assert resonance.vector_similarity == 1.0


def test_cluster_by_resonance():
    graph_a = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={((0, 0), (1, 1)): 1},
    )

    graph_b = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={((0, 0), (1, 1)): 1},
    )

    graph_c = TopologyGraph(
        nodes=((8, 8),),
        edges=(),
        node_weights={(8, 8): 1},
        edge_weights={},
    )

    clusters = cluster_by_resonance(
        {
            "a": graph_a,
            "b": graph_b,
            "c": graph_c,
        },
        threshold=0.95,
    )

    assert clusters[0].members == ("a", "b")
    assert clusters[1].members == ("c",)