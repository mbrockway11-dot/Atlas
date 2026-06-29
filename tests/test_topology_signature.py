from atlas.topology.topology_signature import (
    build_topology_signature,
    compare_topology_signatures,
)


def test_identical_graph_signatures_are_fully_similar():
    graph = {
        "nodes": {
            "1": {
                "weight": 3,
                "cipher_count": 2,
                "planet_count": 3,
                "degree": 2,
                "is_hub": True,
                "is_leaf": False,
                "is_articulation": True,
            },
            "2": {
                "weight": 1,
                "cipher_count": 1,
                "planet_count": 1,
                "degree": 1,
                "is_hub": False,
                "is_leaf": True,
                "is_articulation": False,
            },
        },
        "edges": {
            "1->2": {
                "weight": 2,
                "cipher_count": 1,
                "planet_count": 2,
                "is_bridge": True,
            },
        },
    }

    signature = build_topology_signature(graph)
    similarity = compare_topology_signatures(signature, signature)

    assert similarity.structural_similarity == 1.0
    assert similarity.node_overlap == 1.0
    assert similarity.edge_overlap == 1.0
    assert signature.hub_ids == ("1",)
    assert signature.bridge_ids == ("1->2",)


def test_different_graph_signatures_detect_structural_difference():
    graph_a = {
        "nodes": {
            "1": {
                "weight": 3,
                "cipher_count": 2,
                "planet_count": 3,
                "degree": 2,
                "is_hub": True,
                "is_leaf": False,
                "is_articulation": True,
            },
            "2": {
                "weight": 1,
                "cipher_count": 1,
                "planet_count": 1,
                "degree": 1,
                "is_hub": False,
                "is_leaf": True,
                "is_articulation": False,
            },
        },
        "edges": {
            "1->2": {
                "weight": 2,
                "cipher_count": 1,
                "planet_count": 2,
                "is_bridge": True,
            },
        },
    }

    graph_b = {
        "nodes": {
            "1": {
                "weight": 1,
                "cipher_count": 1,
                "planet_count": 1,
                "degree": 1,
                "is_hub": False,
                "is_leaf": True,
                "is_articulation": False,
            },
            "3": {
                "weight": 5,
                "cipher_count": 3,
                "planet_count": 4,
                "degree": 3,
                "is_hub": True,
                "is_leaf": False,
                "is_articulation": True,
            },
        },
        "edges": {
            "1->3": {
                "weight": 4,
                "cipher_count": 2,
                "planet_count": 2,
                "is_bridge": False,
            },
        },
    }

    signature_a = build_topology_signature(graph_a)
    signature_b = build_topology_signature(graph_b)
    similarity = compare_topology_signatures(signature_a, signature_b)

    assert 0.0 <= similarity.structural_similarity < 1.0
    assert similarity.node_overlap == 1 / 3
    assert similarity.edge_overlap == 0.0