"""Motif statistics utilities."""

from atlas.motifs.catalog import MotifCounts


def total_motifs(motifs: MotifCounts) -> int:
    """Return total detected motif count."""
    return (
        motifs.chains
        + motifs.hubs
        + motifs.loops
        + motifs.bridges
        + motifs.dead_ends
        + motifs.reciprocal_pairs
        + motifs.isolated_nodes
    )


def motif_density(motifs: MotifCounts, node_count: int) -> float:
    """Return motif count divided by node count."""
    if node_count <= 0:
        return 0.0

    return total_motifs(motifs) / node_count


def dominant_motif(motifs: MotifCounts) -> str:
    """Return the dominant motif name."""
    motif_map = {
        "chains": motifs.chains,
        "hubs": motifs.hubs,
        "loops": motifs.loops,
        "bridges": motifs.bridges,
        "dead_ends": motifs.dead_ends,
        "reciprocal_pairs": motifs.reciprocal_pairs,
        "isolated_nodes": motifs.isolated_nodes,
    }

    max_value = max(motif_map.values())

    if max_value == 0:
        return "none"

    for name, value in motif_map.items():
        if value == max_value:
            return name

    return "none"