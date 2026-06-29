from atlas.graph.canonical import (
    CIG_VERSION,
    build_canonical_identity_graph,
    canonical_identity_graph_to_dict,
)


def test_build_canonical_identity_graph_from_minimal_acf():
    acf = {
        "identity": {
            "name": "Test Identity",
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
                    "layer_id": "hebrew_saturn",
                    "cipher": "hebrew",
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

    cig = build_canonical_identity_graph(acf)

    assert cig.version == CIG_VERSION
    assert cig.name == "Test Identity"
    assert cig.raw_graph["summary"]["construction_pass_count"] == 2
    assert cig.summary["construction_pass_count"] == 2
    assert cig.topology_signature.node_count >= 1

    data = canonical_identity_graph_to_dict(cig)

    assert data["version"] == CIG_VERSION
    assert data["name"] == "Test Identity"
    assert "topology_signature" in data
    assert "summary" in data