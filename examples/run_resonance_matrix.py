"""Build a pairwise name resonance matrix."""

import csv
from itertools import combinations
from pathlib import Path

from atlas.ciphers import run_all_ciphers
from atlas.kamea.projection import project_values_to_kamea
from atlas.resonance.resonance import calculate_resonance
from atlas.topology.differential import compare_graphs
from atlas.topology.graph_builder import build_graph_from_kamea_path


OUTPUT_DIR = Path("output/examples/resonance_matrix")
OUTPUT_FILE = OUTPUT_DIR / "name_resonance_matrix.csv"


KAMEA_NAMES = [
    "saturn",
    "jupiter",
    "mars",
    "sun",
    "venus",
    "mercury",
    "moon",
]


def run_resonance_matrix(names: list[str]) -> None:
    """Compare all names pairwise and export resonance scores."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if len(names) < 2:
        raise ValueError("At least two names are required.")

    cipher_results_by_name = {
        name: run_all_ciphers(name)
        for name in names
    }

    rows = []

    for name_a, name_b in combinations(names, 2):
        cipher_results_a = cipher_results_by_name[name_a]
        cipher_results_b = cipher_results_by_name[name_b]

        for cipher_name in cipher_results_a:
            for kamea_name in KAMEA_NAMES:
                graph_a = _build_graph(cipher_results_a[cipher_name], kamea_name)
                graph_b = _build_graph(cipher_results_b[cipher_name], kamea_name)

                diff = compare_graphs(graph_a, graph_b)
                resonance = calculate_resonance(graph_a, graph_b)

                rows.append(
                    {
                        "name_a": name_a,
                        "name_b": name_b,
                        "cipher": cipher_name,
                        "kamea": kamea_name,
                        "overall_resonance": resonance.overall,
                        "node_similarity": resonance.node_similarity,
                        "edge_similarity": resonance.edge_similarity,
                        "node_weight_similarity": resonance.node_weight_similarity,
                        "edge_weight_similarity": resonance.edge_weight_similarity,
                        "vector_similarity": resonance.vector_similarity,
                        "alignment_similarity": resonance.alignment_similarity,
                        "node_overlap_ratio": diff.node_overlap_ratio,
                        "edge_overlap_ratio": diff.edge_overlap_ratio,
                        "shared_node_count": len(diff.shared_nodes),
                        "shared_edge_count": len(diff.shared_edges),
                        "unique_nodes_a": len(diff.unique_nodes_a),
                        "unique_nodes_b": len(diff.unique_nodes_b),
                        "unique_edges_a": len(diff.unique_edges_a),
                        "unique_edges_b": len(diff.unique_edges_b),
                    }
                )

    _write_csv(rows, OUTPUT_FILE)


def _build_graph(values: list[int], kamea_name: str):
    """Build a graph from cipher values and a Kamea name."""
    path = project_values_to_kamea(values, kamea_name)
    return build_graph_from_kamea_path(path)


def _write_csv(rows: list[dict], output_path: Path) -> None:
    """Write matrix rows to CSV."""
    fieldnames = [
        "name_a",
        "name_b",
        "cipher",
        "kamea",
        "overall_resonance",
        "node_similarity",
        "edge_similarity",
        "node_weight_similarity",
        "edge_weight_similarity",
        "vector_similarity",
        "alignment_similarity",
        "node_overlap_ratio",
        "edge_overlap_ratio",
        "shared_node_count",
        "shared_edge_count",
        "unique_nodes_a",
        "unique_nodes_b",
        "unique_edges_a",
        "unique_edges_b",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    run_resonance_matrix(
        [
            "Michael Elvis Brockway",
            "Antonio Ballester",
            "Lance Dean Folks",
            "River Christian Tremblay",
        ]
    )
    print(f"Resonance matrix written to: {OUTPUT_FILE}")