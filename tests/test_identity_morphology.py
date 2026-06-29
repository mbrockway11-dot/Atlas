from atlas.graph.identity_morphology import (
    MORPHOLOGY_VERSION,
    compare_identity_morphology,
    identity_morphology_to_dict,
)
from atlas.graph.identity_stack import build_identity_graph_stack


def _acf(name: str, second_node: int) -> dict:
    return {
        "identity": {
            "name": name,
        },
        "identity_graph": {
            "layers": [
                {
                    "layer_id": f"{name}_ordinal_saturn",
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
                                            "node": second_node,
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


def test_compare_identity_morphology_between_two_stacks():
    stack_a = build_identity_graph_stack(_acf("Morph A", 2))
    stack_b = build_identity_graph_stack(_acf("Morph B", 3))

    morphology = compare_identity_morphology(stack_a, stack_b)

    assert morphology.version == MORPHOLOGY_VERSION
    assert morphology.name_a == "Morph A"
    assert morphology.name_b == "Morph B"

    assert 0.0 <= morphology.node_overlap <= 1.0
    assert 0.0 <= morphology.edge_overlap <= 1.0
    assert 0.0 <= morphology.structural_edit_distance <= 1.0

    assert morphology.morphology_class in {
        "near_isomorphic",
        "local_variation",
        "minor_transformation",
        "moderate_transformation",
        "major_transformation",
        "structural_reconstruction",
    }

    assert "mutation_score" in morphology.motif_mutation
    assert "mutation_score" in morphology.genome_mutation
    assert "mutation_score" in morphology.topology_mutation
    assert "mutation_score" in morphology.resonance_mutation

    data = identity_morphology_to_dict(morphology)

    assert data["version"] == MORPHOLOGY_VERSION
    assert data["name_a"] == "Morph A"
    assert data["name_b"] == "Morph B"
    assert "motif_mutation" in data
    assert "genome_mutation" in data
    assert "topology_mutation" in data
    assert "resonance_mutation" in data
    assert "summary" in data


def test_identical_stacks_are_near_isomorphic():
    acf = _acf("Same Morph", 2)

    stack_a = build_identity_graph_stack(acf)
    stack_b = build_identity_graph_stack(acf)

    morphology = compare_identity_morphology(stack_a, stack_b)

    assert morphology.node_overlap == 1.0
    assert morphology.edge_overlap == 1.0
    assert morphology.structural_edit_distance == 0.0
    assert morphology.morphology_class == "near_isomorphic"