from atlas.classification import (
    classification_to_dict,
    classify_signature,
)
from atlas.signatures.fingerprint import build_topology_signature
from atlas.topology.graph import TopologyGraph


def test_classify_signature_returns_layered_classification():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2)),
        edges=(
            ((0, 0), (1, 1)),
            ((0, 0), (2, 2)),
        ),
        node_weights={(0, 0): 2, (1, 1): 1, (2, 2): 1},
        edge_weights={
            ((0, 0), (1, 1)): 1,
            ((0, 0), (2, 2)): 1,
        },
    )

    signature = build_topology_signature(graph)
    classification = classify_signature(signature)

    assert classification.function.role
    assert classification.expression.expression
    assert classification.state.state
    assert classification.scale == "Individual"


def test_classification_to_dict():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={((0, 0), (1, 1)): 1},
    )

    signature = build_topology_signature(graph)
    classification = classify_signature(signature)
    data = classification_to_dict(classification)

    assert "function" in data
    assert "expression" in data
    assert "state" in data
    assert "scale" in data
    assert "summary" in data