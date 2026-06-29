"""Build topology signatures from graphs."""

from atlas.features.metrics import connected_components, edge_density, graph_symmetry
from atlas.features.scoring import score_graph
from atlas.motifs.detector import detect_motifs
from atlas.motifs.statistics import dominant_motif, motif_density
from atlas.signatures.graph_entropy import node_weight_entropy
from atlas.signatures.motif_detection import (
    branching_level,
    compression_level,
    dominant_pattern,
    reciprocity_level,
)
from atlas.signatures.topology_signature import TopologySignature
from atlas.topology.graph import TopologyGraph


def build_topology_signature(graph: TopologyGraph) -> TopologySignature:
    """Build a deterministic topology signature from a graph."""
    scores = score_graph(graph)
    components = connected_components(graph)
    motifs = detect_motifs(graph)

    return TopologySignature(
        driver=scores.driver,
        amplifier=scores.amplifier,
        regulator=scores.regulator,
        node_count=graph.node_count,
        edge_count=graph.edge_count,
        edge_density=edge_density(graph),
        symmetry=graph_symmetry(graph),
        component_count=len(components),
        entropy=node_weight_entropy(graph),
        dominant_pattern=dominant_pattern(graph),
        branching_level=branching_level(graph),
        reciprocity_level=reciprocity_level(graph),
        compression_level=compression_level(graph),
        dominant_motif=dominant_motif(motifs),
        motif_density=motif_density(motifs, graph.node_count),
        chains=motifs.chains,
        hubs=motifs.hubs,
        loops=motifs.loops,
        bridges=motifs.bridges,
        dead_ends=motifs.dead_ends,
        reciprocal_pairs=motifs.reciprocal_pairs,
        isolated_nodes=motifs.isolated_nodes,
    )