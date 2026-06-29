"""Topology signature objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TopologySignature:
    """Deterministic high-level fingerprint for a topology graph."""

    driver: float
    amplifier: float
    regulator: float

    node_count: int
    edge_count: int
    edge_density: float
    symmetry: float
    component_count: int
    entropy: float

    dominant_pattern: str
    branching_level: str
    reciprocity_level: str
    compression_level: str

    dominant_motif: str
    motif_density: float
    chains: int
    hubs: int
    loops: int
    bridges: int
    dead_ends: int
    reciprocal_pairs: int
    isolated_nodes: int