"""Topology vector objects and builders."""

from dataclasses import dataclass

from atlas.signatures.fingerprint import build_topology_signature
from atlas.topology.graph import TopologyGraph


@dataclass(frozen=True)
class TopologyVector:
    """Numeric vector representation of a topology graph."""

    driver: float
    amplifier: float
    regulator: float
    edge_density: float
    symmetry: float
    entropy: float
    motif_density: float
    chains: float
    hubs: float
    loops: float
    bridges: float
    dead_ends: float
    reciprocal_pairs: float
    isolated_nodes: float


def build_topology_vector(graph: TopologyGraph) -> TopologyVector:
    """Build a deterministic topology vector from a graph."""
    signature = build_topology_signature(graph)

    normalizer = max(1, signature.node_count)

    return TopologyVector(
        driver=signature.driver,
        amplifier=signature.amplifier,
        regulator=signature.regulator,
        edge_density=signature.edge_density,
        symmetry=signature.symmetry,
        entropy=signature.entropy,
        motif_density=signature.motif_density,
        chains=signature.chains / normalizer,
        hubs=signature.hubs / normalizer,
        loops=signature.loops / normalizer,
        bridges=signature.bridges / normalizer,
        dead_ends=signature.dead_ends / normalizer,
        reciprocal_pairs=signature.reciprocal_pairs / normalizer,
        isolated_nodes=signature.isolated_nodes / normalizer,
    )


def vector_to_tuple(vector: TopologyVector) -> tuple[float, ...]:
    """Convert a topology vector to a tuple."""
    return (
        vector.driver,
        vector.amplifier,
        vector.regulator,
        vector.edge_density,
        vector.symmetry,
        vector.entropy,
        vector.motif_density,
        vector.chains,
        vector.hubs,
        vector.loops,
        vector.bridges,
        vector.dead_ends,
        vector.reciprocal_pairs,
        vector.isolated_nodes,
    )