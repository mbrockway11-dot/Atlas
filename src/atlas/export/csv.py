"""CSV export utilities for Atlas objects."""

import csv
from pathlib import Path

from atlas.features.scoring import TopologyScores
from atlas.signatures.topology_signature import TopologySignature
from atlas.topology.graph import TopologyGraph


def export_nodes_csv(graph: TopologyGraph, output_path: str | Path) -> Path:
    """Export graph nodes to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "row",
                "col",
                "weight",
            ],
        )
        writer.writeheader()

        for node in graph.nodes:
            writer.writerow(
                {
                    "row": node[0],
                    "col": node[1],
                    "weight": graph.node_weights.get(node, 0),
                }
            )

    return path


def export_edges_csv(graph: TopologyGraph, output_path: str | Path) -> Path:
    """Export graph edges to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "source_row",
                "source_col",
                "target_row",
                "target_col",
                "weight",
            ],
        )
        writer.writeheader()

        for source, target in graph.edges:
            edge = (source, target)

            writer.writerow(
                {
                    "source_row": source[0],
                    "source_col": source[1],
                    "target_row": target[0],
                    "target_col": target[1],
                    "weight": graph.edge_weights.get(edge, 0),
                }
            )

    return path


def export_scores_csv(scores: TopologyScores, output_path: str | Path) -> Path:
    """Export topology scores to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "driver",
                "amplifier",
                "regulator",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "driver": scores.driver,
                "amplifier": scores.amplifier,
                "regulator": scores.regulator,
            }
        )

    return path


def export_signature_csv(
    signature: TopologySignature,
    output_path: str | Path,
) -> Path:
    """Export topology signature to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "driver",
                "amplifier",
                "regulator",
                "node_count",
                "edge_count",
                "edge_density",
                "symmetry",
                "component_count",
                "entropy",
                "dominant_pattern",
                "branching_level",
                "reciprocity_level",
                "compression_level",
                "dominant_motif",
                "motif_density",
                "chains",
                "hubs",
                "loops",
                "bridges",
                "dead_ends",
                "reciprocal_pairs",
                "isolated_nodes",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "driver": signature.driver,
                "amplifier": signature.amplifier,
                "regulator": signature.regulator,
                "node_count": signature.node_count,
                "edge_count": signature.edge_count,
                "edge_density": signature.edge_density,
                "symmetry": signature.symmetry,
                "component_count": signature.component_count,
                "entropy": signature.entropy,
                "dominant_pattern": signature.dominant_pattern,
                "branching_level": signature.branching_level,
                "reciprocity_level": signature.reciprocity_level,
                "compression_level": signature.compression_level,
                "dominant_motif": signature.dominant_motif,
                "motif_density": signature.motif_density,
                "chains": signature.chains,
                "hubs": signature.hubs,
                "loops": signature.loops,
                "bridges": signature.bridges,
                "dead_ends": signature.dead_ends,
                "reciprocal_pairs": signature.reciprocal_pairs,
                "isolated_nodes": signature.isolated_nodes,
            }
        )

    return path