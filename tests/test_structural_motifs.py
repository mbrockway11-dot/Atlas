from atlas.graph.motifs import (
    MOTIF_VERSION,
    extract_structural_motifs,
    structural_motifs_to_dict,
)


def test_extract_structural_motifs_from_triangle_graph():
    graph = {
        "nodes": {
            "1": {"is_hub": False, "is_leaf": False, "is_articulation": False},
            "2": {"is_hub": False, "is_leaf": False, "is_articulation": False},
            "3": {"is_hub": False, "is_leaf": False, "is_articulation": False},
        },
        "edges": {
            "1->2": {"source": "1", "target": "2", "is_bridge": False},
            "2->3": {"source": "2", "target": "3", "is_bridge": False},
            "3->1": {"source": "3", "target": "1", "is_bridge": False},
        },
    }

    motifs = extract_structural_motifs(graph)

    assert motifs.version == MOTIF_VERSION
    assert motifs.node_count == 3
    assert motifs.edge_count == 3
    assert motifs.triangle_count == 1
    assert motifs.cycle_like_count == 1

    data = structural_motifs_to_dict(motifs)

    assert data["version"] == MOTIF_VERSION
    assert data["summary"]["triangle_count"] == 1


def test_extract_structural_motifs_from_star_graph():
    graph = {
        "nodes": {
            "1": {"is_hub": True, "is_leaf": False, "is_articulation": True},
            "2": {"is_hub": False, "is_leaf": True, "is_articulation": False},
            "3": {"is_hub": False, "is_leaf": True, "is_articulation": False},
            "4": {"is_hub": False, "is_leaf": True, "is_articulation": False},
        },
        "edges": {
            "1->2": {"source": "1", "target": "2", "is_bridge": True},
            "1->3": {"source": "1", "target": "3", "is_bridge": True},
            "1->4": {"source": "1", "target": "4", "is_bridge": True},
        },
    }

    motifs = extract_structural_motifs(graph)

    assert motifs.hub_nodes == ("1",)
    assert motifs.star_count == 1
    assert motifs.bottleneck_count == 4
    assert motifs.summary["leaf_count"] == 3