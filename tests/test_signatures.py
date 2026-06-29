from atlas.signatures.fingerprint import build_topology_signature
from atlas.signatures.graph_entropy import node_weight_entropy
from atlas.signatures.motif_detection import (
    branching_level,
    compression_level,
    dominant_pattern,
    reciprocity_level,
)
from atlas.topology.graph import TopologyGraph


def test_node_weight_entropy_zero_for_empty_graph():
    graph = TopologyGraph(
        nodes=(),
        edges=(),
        node_weights={},
        edge_weights={},
    )

    assert node_weight_entropy(graph) == 0.0


def test_node_weight_entropy_detects_distribution():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={},
    )

    assert node_weight_entropy(graph) == 1.0


def test_motif_detection_reciprocal():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)), ((1, 1), (0, 0))),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={((0, 0), (1, 1)): 1, ((1, 1), (0, 0)): 1},
    )

    assert dominant_pattern(graph) == "reciprocal"
    assert reciprocity_level(graph) == "high"


def test_motif_detection_radiating():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2), (3, 3)),
        edges=(
            ((0, 0), (1, 1)),
            ((0, 0), (2, 2)),
            ((0, 0), (3, 3)),
        ),
        node_weights={(0, 0): 1, (1, 1): 1, (2, 2): 1, (3, 3): 1},
        edge_weights={
            ((0, 0), (1, 1)): 1,
            ((0, 0), (2, 2)): 1,
            ((0, 0), (3, 3)): 1,
        },
    )

    assert dominant_pattern(graph) == "radiating"
    assert branching_level(graph) == "medium"


def test_compression_level_high():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2)),
        edges=(
            ((0, 0), (1, 1)),
            ((1, 1), (0, 0)),
            ((0, 0), (2, 2)),
        ),
        node_weights={(0, 0): 1, (1, 1): 1, (2, 2): 1},
        edge_weights={
            ((0, 0), (1, 1)): 1,
            ((1, 1), (0, 0)): 1,
            ((0, 0), (2, 2)): 1,
        },
    )

    assert compression_level(graph) == "high"


def test_build_topology_signature():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)), ((1, 1), (0, 0))),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={((0, 0), (1, 1)): 1, ((1, 1), (0, 0)): 1},
    )

    signature = build_topology_signature(graph)

    assert signature.node_count == 2
    assert signature.edge_count == 2
    assert signature.dominant_pattern == "reciprocal"
    assert signature.reciprocity_level == "high"
    assert signature.component_count == 1
    assert signature.entropy == 1.0

    assert signature.dominant_motif == "chains"
    assert signature.motif_density == 1.5
    assert signature.chains == 2
    assert signature.hubs == 0
    assert signature.loops == 0
    assert signature.bridges == 0
    assert signature.dead_ends == 0
    assert signature.reciprocal_pairs == 1
    assert signature.isolated_nodes == 0