from atlas.features.scoring import score_graph
from atlas.topology.graph import TopologyGraph


def test_empty_graph_scores_zero():
    graph = TopologyGraph(
        nodes=(),
        edges=(),
        node_weights={},
        edge_weights={},
    )

    scores = score_graph(graph)

    assert scores.driver == 0.0
    assert scores.amplifier == 0.0
    assert scores.regulator == 0.0


def test_driver_score_detects_outward_force():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2)),
        edges=(((0, 0), (1, 1)), ((0, 0), (2, 2))),
        node_weights={(0, 0): 1, (1, 1): 1, (2, 2): 1},
        edge_weights={
            ((0, 0), (1, 1)): 1,
            ((0, 0), (2, 2)): 1,
        },
    )

    scores = score_graph(graph)

    assert scores.driver == 1.0


def test_amplifier_score_uses_repetition_and_density():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 2, (1, 1): 1},
        edge_weights={((0, 0), (1, 1)): 3},
    )

    scores = score_graph(graph)

    assert scores.amplifier > 0.0
    assert scores.amplifier <= 1.0


def test_regulator_score_rewards_balance_and_symmetry():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)), ((1, 1), (0, 0))),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={
            ((0, 0), (1, 1)): 1,
            ((1, 1), (0, 0)): 1,
        },
    )

    scores = score_graph(graph)

    assert scores.regulator == 1.0


def test_scores_are_clamped_between_zero_and_one():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 100, (1, 1): 100},
        edge_weights={((0, 0), (1, 1)): 100},
    )

    scores = score_graph(graph)

    assert 0.0 <= scores.driver <= 1.0
    assert 0.0 <= scores.amplifier <= 1.0
    assert 0.0 <= scores.regulator <= 1.0