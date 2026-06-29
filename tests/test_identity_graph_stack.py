from atlas.graph.identity_stack import (
    STACK_VERSION,
    build_identity_graph_stack,
    identity_graph_stack_to_dict,
)


def test_build_identity_graph_stack_from_minimal_acf():
    acf = {
        "identity": {
            "name": "Stack Test",
        },
        "identity_graph": {
            "layers": [
                {
                    "layer_id": "ordinal_saturn",
                    "cipher": "ordinal",
                    "planet": "Saturn",
                    "features": {
                        "path_views": {
                            "analysis_path": {
                                "visit_history": {
                                    "visits": [
                                        {
                                            "node": 1,
                                            "coordinate": [0, 0],
                                            "sequence_index": 0,
                                            "visit_depth": 1,
                                        },
                                        {
                                            "node": 2,
                                            "coordinate": [0, 1],
                                            "sequence_index": 1,
                                            "visit_depth": 1,
                                        },
                                        {
                                            "node": 1,
                                            "coordinate": [0, 0],
                                            "sequence_index": 2,
                                            "visit_depth": 2,
                                        },
                                    ]
                                }
                            }
                        }
                    },
                },
                {
                    "layer_id": "hebrew_mars",
                    "cipher": "hebrew",
                    "planet": "Mars",
                    "features": {
                        "path_views": {
                            "analysis_path": {
                                "visit_history": {
                                    "visits": [
                                        {
                                            "node": 1,
                                            "coordinate": [0, 0],
                                            "sequence_index": 0,
                                            "visit_depth": 1,
                                        },
                                        {
                                            "node": 3,
                                            "coordinate": [1, 0],
                                            "sequence_index": 1,
                                            "visit_depth": 1,
                                        },
                                    ]
                                }
                            }
                        }
                    },
                },
            ]
        },
    }

    stack = build_identity_graph_stack(acf)

    assert stack.version == STACK_VERSION
    assert stack.name == "Stack Test"
    assert stack.cig.name == "Stack Test"
    assert stack.stg.name == "Stack Test"
    assert stack.genome.name == "Stack Test"
    assert stack.topology.name == "Stack Test"
    assert stack.resonance.name == "Stack Test"

    data = identity_graph_stack_to_dict(stack)

    assert data["version"] == STACK_VERSION
    assert data["name"] == "Stack Test"
    assert "cig" in data
    assert "stg" in data
    assert "motifs" in data
    assert "genome" in data
    assert "topology" in data
    assert "resonance" in data
    assert "summary" in data