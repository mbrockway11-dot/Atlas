import json

from atlas.export.json import (
    export_comparison_json,
    export_resonance_json,
    resonance_to_dict,
)
from atlas.resonance.resonance import calculate_resonance
from atlas.topology.differential import compare_graphs
from atlas.topology.graph import TopologyGraph


def test_resonance_to_dict_is_json_safe():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={((0, 0), (1, 1)): 1},
    )

    resonance = calculate_resonance(graph, graph)
    data = resonance_to_dict(resonance)

    assert data["overall"] == 1.0
    assert data["node_similarity"] == 1.0
    assert data["edge_similarity"] == 1.0
    assert data["node_weight_similarity"] == 1.0
    assert data["edge_weight_similarity"] == 1.0
    assert data["vector_similarity"] == 1.0
    assert data["alignment_similarity"] == 1.0


def test_export_resonance_json(tmp_path):
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={((0, 0), (1, 1)): 1},
    )

    resonance = calculate_resonance(graph, graph)

    output_path = tmp_path / "resonance.json"
    export_resonance_json(resonance, output_path)

    with output_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data["overall"] == 1.0
    assert data["alignment_similarity"] == 1.0


def test_export_comparison_json(tmp_path):
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
    resonance = calculate_resonance(graph_a, graph_b)

    output_path = tmp_path / "comparison.json"
    export_comparison_json(graph_a, graph_b, diff, resonance, output_path)

    with output_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert "graph_a" in data
    assert "graph_b" in data
    assert "differential" in data
    assert "resonance" in data