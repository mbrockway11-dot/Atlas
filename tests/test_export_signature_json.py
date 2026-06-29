import json

from atlas.export.json import (
    export_graph_with_signature_json,
    export_signature_json,
    signature_to_dict,
)
from atlas.signatures.fingerprint import build_topology_signature
from atlas.topology.graph import TopologyGraph


def test_signature_to_dict_is_json_safe():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)), ((1, 1), (0, 0))),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={
            ((0, 0), (1, 1)): 1,
            ((1, 1), (0, 0)): 1,
        },
    )

    signature = build_topology_signature(graph)
    data = signature_to_dict(signature)

    assert data["scores"]["driver"] == signature.driver
    assert data["scores"]["amplifier"] == signature.amplifier
    assert data["scores"]["regulator"] == signature.regulator

    assert data["metrics"]["node_count"] == 2
    assert data["metrics"]["edge_count"] == 2
    assert data["metrics"]["component_count"] == 1
    assert data["metrics"]["entropy"] == 1.0

    assert data["patterns"]["dominant_pattern"] == "reciprocal"
    assert data["patterns"]["reciprocity_level"] == "high"

    assert data["motifs"]["dominant_motif"] == "chains"
    assert data["motifs"]["reciprocal_pairs"] == 1


def test_export_signature_json(tmp_path):
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={((0, 0), (1, 1)): 1},
    )

    signature = build_topology_signature(graph)

    output_path = tmp_path / "signature.json"
    export_signature_json(signature, output_path)

    with output_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert "scores" in data
    assert "metrics" in data
    assert "patterns" in data
    assert "motifs" in data


def test_export_graph_with_signature_json(tmp_path):
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={((0, 0), (1, 1)): 1},
    )

    signature = build_topology_signature(graph)

    output_path = tmp_path / "graph_signature.json"
    export_graph_with_signature_json(graph, signature, output_path)

    with output_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data["graph"]["nodes"] == [[0, 0], [1, 1]]
    assert "signature" in data
    assert "scores" in data["signature"]
    assert "metrics" in data["signature"]
    assert "patterns" in data["signature"]
    assert "motifs" in data["signature"]