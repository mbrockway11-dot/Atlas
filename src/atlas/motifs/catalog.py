"""Motif catalog definitions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MotifCounts:
    """Detected motif counts for a topology graph."""

    chains: int
    hubs: int
    loops: int
    bridges: int
    dead_ends: int
    reciprocal_pairs: int
    isolated_nodes: int