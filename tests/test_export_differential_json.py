import json

from atlas.export.json import differential_to_dict, export_differential_json
from atlas.topology.differential import compare_graphs
from atlas.topology.graph import TopologyGraph


def test_differential_to_dict_is_json_safe():
    edge_a = ((0, 0), (1, 1))
    edge_b = ((1, 1), (2, 2))

    graph_a = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(edge_a,),
        node_weights={(0, 0): 1, (1, 1): 3},
        edge_weights={edge_a: 2},
    )

    graph_b = TopologyGraph(
        nodes=((1, 1), (2, 2)),
        edges=(edge_b,),
        node_weights={(1, 1): 1, (2, 2): 5},
        edge_weights={edge_b: 7},
    )

    diff = compare_graphs(graph_a, graph_b)
    data = differential_to_dict(diff)

    assert data["shared_nodes"] == [[1, 1]]
    assert data["shared_edges"] == []

    assert data["unique_nodes_a"] == [[0, 0]]
    assert data["unique_nodes_b"] == [[2, 2]]

    assert data["unique_edges_a"] == [[[0, 0], [1, 1]]]
    assert data["unique_edges_b"] == [[[1, 1], [2, 2]]]

    assert data["overlap"]["node_overlap_ratio"] == 1 / 3
    assert data["overlap"]["edge_overlap_ratio"] == 0.0


def test_export_differential_json(tmp_path):
    edge_a = ((0, 0), (1, 1))
    edge_b = ((1, 1), (0, 0))

    graph_a = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(edge_a,),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={edge_a: 1},
    )

    graph_b = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(edge_b,),
        node_weights={(0, 0): 2, (1, 1): 1},
        edge_weights={edge_b: 3},
    )

    diff = compare_graphs(graph_a, graph_b)

    output_path = tmp_path / "diff.json"
    export_differential_json(diff, output_path)

    with output_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data["shared_nodes"] == [[0, 0], [1, 1]]
    assert data["unique_edges_a"] == [[[0, 0], [1, 1]]]
    assert data["unique_edges_b"] == [[[1, 1], [0, 0]]]