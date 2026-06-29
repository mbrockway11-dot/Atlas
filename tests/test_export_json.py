import json

from atlas.export.json import (
    export_graph_json,
    export_graph_with_scores_json,
    export_scores_json,
    graph_to_dict,
    scores_to_dict,
)
from atlas.features.scoring import TopologyScores
from atlas.topology.graph import TopologyGraph


def test_graph_to_dict_is_json_safe():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 2, (1, 1): 1},
        edge_weights={((0, 0), (1, 1)): 3},
    )

    data = graph_to_dict(graph)

    assert data["nodes"] == [[0, 0], [1, 1]]
    assert data["edges"] == [[[0, 0], [1, 1]]]

    assert data["node_weights"] == [
        {"node": [0, 0], "weight": 2},
        {"node": [1, 1], "weight": 1},
    ]

    assert data["edge_weights"] == [
        {"edge": [[0, 0], [1, 1]], "weight": 3},
    ]

    assert data["summary"]["node_count"] == 2
    assert data["summary"]["edge_count"] == 1


def test_scores_to_dict():
    scores = TopologyScores(
        driver=0.1,
        amplifier=0.2,
        regulator=0.3,
    )

    assert scores_to_dict(scores) == {
        "driver": 0.1,
        "amplifier": 0.2,
        "regulator": 0.3,
    }


def test_export_graph_json(tmp_path):
    graph = TopologyGraph(
        nodes=((0, 0),),
        edges=(),
        node_weights={(0, 0): 1},
        edge_weights={},
    )

    output_path = tmp_path / "graph.json"
    result_path = export_graph_json(graph, output_path)

    assert result_path == output_path
    assert output_path.exists()

    with output_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data["nodes"] == [[0, 0]]
    assert data["summary"]["node_count"] == 1


def test_export_scores_json(tmp_path):
    scores = TopologyScores(
        driver=1.0,
        amplifier=0.5,
        regulator=0.25,
    )

    output_path = tmp_path / "scores.json"
    export_scores_json(scores, output_path)

    with output_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data == {
        "amplifier": 0.5,
        "driver": 1.0,
        "regulator": 0.25,
    }


def test_export_graph_with_scores_json(tmp_path):
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={((0, 0), (1, 1)): 1},
    )

    scores = TopologyScores(
        driver=1.0,
        amplifier=0.25,
        regulator=0.5,
    )

    output_path = tmp_path / "combined.json"
    export_graph_with_scores_json(graph, scores, output_path)

    with output_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data["graph"]["nodes"] == [[0, 0], [1, 1]]
    assert data["scores"]["driver"] == 1.0