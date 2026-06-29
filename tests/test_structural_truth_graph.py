from atlas.graph.canonical import build_canonical_identity_graph
from atlas.graph.structural_truth import (
    STG_VERSION,
    build_structural_truth_graph,
    structural_truth_graph_to_dict,
)


def test_build_structural_truth_graph_from_cig():
    acf = {
        "identity": {
            "name": "Truth Test",
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
                }
            ]
        },
    }

    cig = build_canonical_identity_graph(acf)

    stg = build_structural_truth_graph(
        cig,
        min_node_truth_score=0.0,
        min_edge_truth_score=0.0,
    )

    assert stg.version == STG_VERSION
    assert stg.name == "Truth Test"
    assert stg.summary["source_node_count"] >= stg.summary["truth_node_count"]
    assert stg.summary["source_edge_count"] >= stg.summary["truth_edge_count"]

    data = structural_truth_graph_to_dict(stg)

    assert data["version"] == STG_VERSION
    assert "nodes" in data
    assert "edges" in data
    assert "summary" in data