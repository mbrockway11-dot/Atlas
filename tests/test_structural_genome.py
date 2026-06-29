from atlas.graph.structural_genome import (
    GENOME_VERSION,
    build_structural_genome,
    structural_genome_to_dict,
)
from atlas.graph.structural_truth import StructuralTruthGraph


def test_build_structural_genome_from_truth_graph():
    stg = StructuralTruthGraph(
        version="1.0",
        name="Genome Test",
        nodes={
            "1": {
                "id": "1",
                "is_hub": True,
                "is_leaf": False,
                "is_articulation": True,
                "truth": {"score": 0.9},
            },
            "2": {
                "id": "2",
                "is_hub": False,
                "is_leaf": True,
                "is_articulation": False,
                "truth": {"score": 0.5},
            },
            "3": {
                "id": "3",
                "is_hub": False,
                "is_leaf": True,
                "is_articulation": False,
                "truth": {"score": 0.5},
            },
            "4": {
                "id": "4",
                "is_hub": False,
                "is_leaf": True,
                "is_articulation": False,
                "truth": {"score": 0.5},
            },
        },
        edges={
            "1->2": {
                "id": "1->2",
                "source": "1",
                "target": "2",
                "is_bridge": True,
                "truth": {"score": 0.7},
            },
            "1->3": {
                "id": "1->3",
                "source": "1",
                "target": "3",
                "is_bridge": True,
                "truth": {"score": 0.7},
            },
            "1->4": {
                "id": "1->4",
                "source": "1",
                "target": "4",
                "is_bridge": True,
                "truth": {"score": 0.7},
            },
        },
        summary={},
    )

    genome = build_structural_genome(stg)

    assert genome.version == GENOME_VERSION
    assert genome.name == "Genome Test"
    assert genome.node_count == 4
    assert genome.edge_count == 3
    assert genome.hub_count == 1
    assert genome.bridge_count == 3
    assert genome.star_count == 1
    assert genome.persistence_score > 0
    assert genome.genome_sequence

    data = structural_genome_to_dict(genome)

    assert data["version"] == GENOME_VERSION
    assert data["summary"]["dominant_motif"] is not None