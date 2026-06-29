from atlas.motifs.detector import (
    count_bridge_edges,
    count_chain_nodes,
    count_dead_ends,
    count_hubs,
    count_isolated_nodes,
    count_reciprocal_pairs,
    count_self_loops,
    detect_motifs,
)
from atlas.motifs.statistics import dominant_motif, motif_density, total_motifs
from atlas.topology.graph import TopologyGraph


def test_detect_chain_and_dead_end():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2)),
        edges=(((0, 0), (1, 1)), ((1, 1), (2, 2))),
        node_weights={(0, 0): 1, (1, 1): 1, (2, 2): 1},
        edge_weights={((0, 0), (1, 1)): 1, ((1, 1), (2, 2)): 1},
    )

    assert count_chain_nodes(graph) == 1
    assert count_dead_ends(graph) == 1
    assert count_bridge_edges(graph) == 2


def test_detect_hub():
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

    assert count_hubs(graph) == 1


def test_detect_self_loop_and_reciprocal_pair():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(
            ((0, 0), (0, 0)),
            ((0, 0), (1, 1)),
            ((1, 1), (0, 0)),
        ),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={
            ((0, 0), (0, 0)): 1,
            ((0, 0), (1, 1)): 1,
            ((1, 1), (0, 0)): 1,
        },
    )

    assert count_self_loops(graph) == 1
    assert count_reciprocal_pairs(graph) == 1


def test_detect_isolated_node():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2)),
        edges=(((0, 0), (1, 1)),),
        node_weights={(0, 0): 1, (1, 1): 1, (2, 2): 1},
        edge_weights={((0, 0), (1, 1)): 1},
    )

    assert count_isolated_nodes(graph) == 1


def test_detect_motifs_bundle():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2)),
        edges=(((0, 0), (1, 1)), ((1, 1), (2, 2))),
        node_weights={(0, 0): 1, (1, 1): 1, (2, 2): 1},
        edge_weights={((0, 0), (1, 1)): 1, ((1, 1), (2, 2)): 1},
    )

    motifs = detect_motifs(graph)

    assert motifs.chains == 1
    assert motifs.dead_ends == 1
    assert motifs.bridges == 2


def test_motif_statistics():
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1), (2, 2)),
        edges=(((0, 0), (1, 1)), ((1, 1), (2, 2))),
        node_weights={(0, 0): 1, (1, 1): 1, (2, 2): 1},
        edge_weights={((0, 0), (1, 1)): 1, ((1, 1), (2, 2)): 1},
    )

    motifs = detect_motifs(graph)

    assert total_motifs(motifs) == 4
    assert motif_density(motifs, graph.node_count) == 4 / 3
    assert dominant_motif(motifs) == "bridges"