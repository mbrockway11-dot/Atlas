import csv

from atlas.export.csv import (
    export_edges_csv,
    export_nodes_csv,
    export_scores_csv,
)
from atlas.features.scoring import TopologyScores
from atlas.topology.graph import TopologyGraph


def test_export_nodes_csv(tmp_path):
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(),
        node_weights={(0, 0): 2, (1, 1): 3},
        edge_weights={},
    )

    output_path = tmp_path / "nodes.csv"
    export_nodes_csv(graph, output_path)

    with output_path.open("r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert rows == [
        {"row": "0", "col": "0", "weight": "2"},
        {"row": "1", "col": "1", "weight": "3"},
    ]


def test_export_edges_csv(tmp_path):
    edge = ((0, 0), (1, 1))

    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(edge,),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={edge: 5},
    )

    output_path = tmp_path / "edges.csv"
    export_edges_csv(graph, output_path)

    with output_path.open("r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert rows == [
        {
            "source_row": "0",
            "source_col": "0",
            "target_row": "1",
            "target_col": "1",
            "weight": "5",
        }
    ]


def test_export_scores_csv(tmp_path):
    scores = TopologyScores(
        driver=1.0,
        amplifier=0.5,
        regulator=0.25,
    )

    output_path = tmp_path / "scores.csv"
    export_scores_csv(scores, output_path)

    with output_path.open("r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert rows == [
        {
            "driver": "1.0",
            "amplifier": "0.5",
            "regulator": "0.25",
        }
    ]