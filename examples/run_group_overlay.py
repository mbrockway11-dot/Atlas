"""Build group overlays across all ciphers and Kameas."""

from pathlib import Path

from atlas.ciphers import run_all_ciphers
from atlas.export.csv import export_edges_csv, export_nodes_csv, export_scores_csv
from atlas.export.json import export_graph_with_signature_json
from atlas.export.svg import export_graph_svg_3d
from atlas.features.scoring import score_graph
from atlas.kamea.projection import get_kamea, project_values_to_kamea
from atlas.signatures.fingerprint import build_topology_signature
from atlas.topology.graph_builder import build_graph_from_kamea_path
from atlas.topology.overlay import overlay_graphs


OUTPUT_DIR = Path("output/examples/group_overlay")


def run_group_overlay(names: list[str]) -> None:
    """Build group topology overlays across all ciphers and Kameas."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not names:
        raise ValueError("At least one name is required.")

    cipher_results_by_name = {
        name: run_all_ciphers(name)
        for name in names
    }

    cipher_names = list(next(iter(cipher_results_by_name.values())).keys())

    for cipher_name in cipher_names:
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
            graphs = []

            for name in names:
                values = cipher_results_by_name[name][cipher_name]
                path = project_values_to_kamea(values, kamea_name)
                graph = build_graph_from_kamea_path(path)
                graphs.append(graph)

            overlay_graph = overlay_graphs(graphs)
            scores = score_graph(overlay_graph)
            signature = build_topology_signature(overlay_graph)

            base_path = OUTPUT_DIR / (
                f"{_safe_group_name(names)}"
                f"_{cipher_name}"
                f"_{kamea.key}"
                f"_group_overlay"
            )

            export_graph_with_signature_json(
                graph=overlay_graph,
                signature=signature,
                output_path=base_path.with_suffix(".json"),
            )

            export_nodes_csv(
                graph=overlay_graph,
                output_path=OUTPUT_DIR / f"{base_path.name}_nodes.csv",
            )

            export_edges_csv(
                graph=overlay_graph,
                output_path=OUTPUT_DIR / f"{base_path.name}_edges.csv",
            )

            export_scores_csv(
                scores=scores,
                output_path=OUTPUT_DIR / f"{base_path.name}_scores.csv",
            )

            export_graph_svg_3d(
                graph=overlay_graph,
                output_path=base_path.with_suffix(".svg"),
                grid_size=kamea.size,
            )


def _safe_group_name(names: list[str]) -> str:
    """Create a safe filename stem for a group."""
    return "__".join(_safe_name(name) for name in names)


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
    run_group_overlay(
        [
            "Michael Elvis Brockway",
            "Antonio Ballester",
            "Lance Dean Folks",
        ]
    )
    print(f"Group overlay exports written to: {OUTPUT_DIR}")