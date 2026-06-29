"""End-to-end Atlas name pipeline example."""

from pathlib import Path

from atlas.ciphers import run_all_ciphers
from atlas.export.csv import export_edges_csv, export_nodes_csv, export_scores_csv
from atlas.export.json import export_graph_with_signature_json
from atlas.export.svg import export_graph_svg_3d
from atlas.features.scoring import score_graph
from atlas.kamea.projection import get_kamea, project_values_to_kamea
from atlas.signatures.fingerprint import build_topology_signature
from atlas.topology.graph_builder import build_graph_from_kamea_path


OUTPUT_DIR = Path("output/examples/name_pipeline")


def run_name_pipeline(name: str) -> None:
    """Run all ciphers through all Kameas and export results."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cipher_results = run_all_ciphers(name)

    for cipher_name, values in cipher_results.items():
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
            path = project_values_to_kamea(values, kamea_name)
            graph = build_graph_from_kamea_path(path)
            scores = score_graph(graph)
            signature = build_topology_signature(graph)

            base_path = OUTPUT_DIR / f"{_safe_name(name)}_{cipher_name}_{kamea_name}"

            export_graph_with_signature_json(
                graph=graph,
                signature=signature,
                output_path=base_path.with_suffix(".json"),
            )

            export_nodes_csv(
                graph=graph,
                output_path=OUTPUT_DIR / f"{base_path.name}_nodes.csv",
            )

            export_edges_csv(
                graph=graph,
                output_path=OUTPUT_DIR / f"{base_path.name}_edges.csv",
            )

            export_scores_csv(
                scores=scores,
                output_path=OUTPUT_DIR / f"{base_path.name}_scores.csv",
            )

            export_graph_svg_3d(
                graph=graph,
                output_path=base_path.with_suffix(".svg"),
                grid_size=kamea.size,
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
    run_name_pipeline("Michael Elvis Brockway")
    print(f"Exports written to: {OUTPUT_DIR}")