"""Compare two names across all ciphers and Kameas."""

from pathlib import Path

from atlas.ciphers import run_all_ciphers
from atlas.export.json import export_comparison_json
from atlas.kamea.projection import get_kamea, project_values_to_kamea
from atlas.resonance.resonance import calculate_resonance
from atlas.topology.differential import compare_graphs
from atlas.topology.graph_builder import build_graph_from_kamea_path


OUTPUT_DIR = Path("output/examples/name_comparison")


def run_compare_names(name_a: str, name_b: str) -> None:
    """Compare two names across matching cipher and Kamea projections."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cipher_results_a = run_all_ciphers(name_a)
    cipher_results_b = run_all_ciphers(name_b)

    for cipher_name in cipher_results_a:
        values_a = cipher_results_a[cipher_name]
        values_b = cipher_results_b[cipher_name]

        for kamea_name in [
            "saturn",
            "jupiter",
            "mars",
            "sun",
            "venus",
            "mercury",
            "moon",
        ]:
            kamea = get_kamea(kamea_name)

            path_a = project_values_to_kamea(values_a, kamea_name)
            path_b = project_values_to_kamea(values_b, kamea_name)

            graph_a = build_graph_from_kamea_path(path_a)
            graph_b = build_graph_from_kamea_path(path_b)

            diff = compare_graphs(graph_a, graph_b)
            resonance = calculate_resonance(graph_a, graph_b)

            output_path = OUTPUT_DIR / (
                f"{_safe_name(name_a)}"
                f"_vs_"
                f"{_safe_name(name_b)}"
                f"_{cipher_name}"
                f"_{kamea.key}"
                f"_comparison.json"
            )

            export_comparison_json(
                graph_a=graph_a,
                graph_b=graph_b,
                diff=diff,
                resonance=resonance,
                output_path=output_path,
            )


def _safe_name(name: str) -> str:
    """Create a safe lowercase filename stem."""
    return (
        name.lower()
        .strip()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("'", "")
    )


if __name__ == "__main__":
    run_compare_names(
        "Michael Elvis Brockway",
        "Antonio Ballester",
    )
    print(f"Comparison exports written to: {OUTPUT_DIR}")