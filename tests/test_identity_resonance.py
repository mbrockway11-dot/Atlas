from atlas.graph.identity_resonance import (
    RESONANCE_VERSION,
    build_identity_resonance,
    identity_resonance_to_dict,
)
from atlas.graph.identity_topology import IdentityTopology


def test_build_identity_resonance_from_topology():
    topology = IdentityTopology(
        version="1.0",
        name="Resonance Test",
        topology_class="hierarchical_bottleneck",
        dominant_axis="persistence",
        flow_pattern="channeled",
        organization_pattern="centralized",
        stability_pattern="high_persistence",
        hierarchy_score=0.6,
        branching_score=0.4,
        cyclicity_score=0.1,
        bottleneck_score=0.5,
        persistence_score=0.8,
        topology_vector={
            "hierarchy": 0.6,
            "branching": 0.4,
            "cyclicity": 0.1,
            "bottleneck": 0.5,
            "persistence": 0.8,
            "motif_richness": 0.5,
        },
        summary={},
    )

    resonance = build_identity_resonance(topology)

    assert resonance.version == RESONANCE_VERSION
    assert resonance.name == "Resonance Test"
    assert resonance.resonance_vector["activation"] > 0
    assert resonance.resonance_vector["propagation"] > 0
    assert resonance.dominant_resonance_axis in resonance.resonance_vector

    data = identity_resonance_to_dict(resonance)

    assert data["version"] == RESONANCE_VERSION
    assert data["summary"]["source"] == "IdentityTopology"


def test_low_topology_classifies_as_low_resonance():
    topology = IdentityTopology(
        version="1.0",
        name="Low Resonance Test",
        topology_class="distributed_sparse",
        dominant_axis="persistence",
        flow_pattern="diffuse",
        organization_pattern="distributed",
        stability_pattern="low_persistence",
        hierarchy_score=0.0,
        branching_score=0.0,
        cyclicity_score=0.0,
        bottleneck_score=0.0,
        persistence_score=0.1,
        topology_vector={
            "hierarchy": 0.0,
            "branching": 0.0,
            "cyclicity": 0.0,
            "bottleneck": 0.0,
            "persistence": 0.1,
            "motif_richness": 0.0,
        },
        summary={},
    )

    resonance = build_identity_resonance(topology)

    assert resonance.resonance_class == "low_resonance"
    assert resonance.activation_pattern == "low_activation"