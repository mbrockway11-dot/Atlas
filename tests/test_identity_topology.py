from atlas.graph.identity_topology import (
    TOPOLOGY_VERSION,
    build_identity_topology,
    identity_topology_to_dict,
)
from atlas.graph.structural_genome import StructuralGenome


def test_build_identity_topology_from_structural_genome():
    genome = StructuralGenome(
        version="1.0",
        name="Topology Test",
        node_count=4,
        edge_count=3,
        hub_count=1,
        bridge_count=3,
        articulation_count=1,
        leaf_count=3,
        chain_count=0,
        triangle_count=0,
        star_count=1,
        bottleneck_count=4,
        cycle_like_count=0,
        motif_richness=0.5,
        hierarchy_score=0.6,
        branching_score=0.4,
        cyclicity_score=0.0,
        bottleneck_score=0.5,
        persistence_score=0.8,
        genome_sequence=("bottleneck", "leaf", "bridge", "hub"),
        summary={},
    )

    topology = build_identity_topology(genome)

    assert topology.version == TOPOLOGY_VERSION
    assert topology.name == "Topology Test"
    assert topology.topology_class == "hierarchical_bottleneck"
    assert topology.flow_pattern == "channeled"
    assert topology.organization_pattern == "centralized"
    assert topology.stability_pattern == "high_persistence"
    assert topology.dominant_axis in topology.topology_vector

    data = identity_topology_to_dict(topology)

    assert data["version"] == TOPOLOGY_VERSION
    assert data["summary"]["source"] == "StructuralGenome"


def test_sparse_genome_classifies_as_distributed_sparse():
    genome = StructuralGenome(
        version="1.0",
        name="Sparse Test",
        node_count=2,
        edge_count=1,
        hub_count=0,
        bridge_count=0,
        articulation_count=0,
        leaf_count=0,
        chain_count=0,
        triangle_count=0,
        star_count=0,
        bottleneck_count=0,
        cycle_like_count=0,
        motif_richness=0.0,
        hierarchy_score=0.0,
        branching_score=0.0,
        cyclicity_score=0.0,
        bottleneck_score=0.0,
        persistence_score=0.1,
        genome_sequence=(),
        summary={},
    )

    topology = build_identity_topology(genome)

    assert topology.topology_class == "distributed_sparse"
    assert topology.flow_pattern == "diffuse"