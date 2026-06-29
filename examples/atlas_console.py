"""Interactive Atlas console."""

from pathlib import Path

from atlas.ciphers import run_all_ciphers
from atlas.essence.profile import build_essence_profile
from atlas.export.composite_svg import CompositeImageCell, export_composite_svg
from atlas.export.csv import export_edges_csv, export_nodes_csv, export_scores_csv
from atlas.export.json import (
    export_comparison_json,
    export_graph_with_signature_json,
    write_json,
)
from atlas.export.svg import export_graph_svg_3d
from atlas.features.scoring import score_graph
from atlas.interpretation.profile import (
    interpret_profile_summary,
    profile_interpretation_to_dict,
)
from atlas.kamea.projection import get_kamea, project_values_to_kamea
from atlas.library.profile_library import (
    list_saved_profiles,
    load_profile_interpretation,
    profile_exists,
    save_profile_to_library,
    safe_name,
)
from atlas.profiles.composite import write_composite_profile_manifest
from atlas.profiles.summary import build_individual_profile_summary
from atlas.reports.markdown import build_profile_markdown_report, write_markdown_report
from atlas.resonance.resonance import calculate_resonance
from atlas.signatures.fingerprint import build_topology_signature
from atlas.topology.differential import compare_graphs
from atlas.topology.graph_builder import build_graph_from_kamea_path
from atlas.topology.overlay import overlay_graphs


KAMEA_NAMES = [
    "saturn",
    "jupiter",
    "mars",
    "sun",
    "venus",
    "mercury",
    "moon",
]

CIPHER_ORDER = [
    "ordinal",
    "hebrew_literal",
    "hebrew_phonetic",
]


def main() -> None:
    """Run the interactive Atlas console."""
    while True:
        print_header()

        choice = input(
            "Choose:\n"
            "1) Build individual Codex profile\n"
            "2) Compare two profiles\n"
            "3) Build group overlay\n"
            "4) Save profile to library\n"
            "5) List saved profiles\n"
            "6) View saved profile summary\n"
            "7) Exit\n"
            "> "
        ).strip()

        if choice == "1":
            name = input("Enter name: ").strip()
            if name:
                build_individual_profile(name)

        elif choice == "2":
            name_a = input("Enter first name: ").strip()
            name_b = input("Enter second name: ").strip()
            if name_a and name_b:
                compare_profiles(name_a, name_b)

        elif choice == "3":
            raw_names = input("Enter names separated by commas: ").strip()
            names = [name.strip() for name in raw_names.split(",") if name.strip()]
            if names:
                build_group_overlay(names)

        elif choice == "4":
            name = input("Enter name to save to library: ").strip()
            if name:
                save_profile(name)

        elif choice == "5":
            show_saved_profiles()

        elif choice == "6":
            profile_key = input("Enter saved profile key: ").strip()
            if profile_key:
                show_saved_profile_summary(profile_key)

        elif choice == "7":
            print("Exiting Atlas.")
            break

        else:
            print("Invalid choice.")

        input("\nPress Enter to continue...")


def print_header() -> None:
    """Print console header."""
    print("\n" + "=" * 50)
    print("ATLAS")
    print("Deterministic Symbolic Topology Console")
    print("=" * 50)


def build_individual_profile(name: str) -> None:
    """Build one complete individual Codex profile."""
    output_dir = Path("output/console/individual") / safe_name(name)
    output_dir.mkdir(parents=True, exist_ok=True)

    composite_cells: list[CompositeImageCell] = []
    cipher_results = run_all_ciphers(name)

    for cipher_name, values in cipher_results.items():
        for kamea_name in KAMEA_NAMES:
            kamea = get_kamea(kamea_name)
            graph = build_graph(values, kamea_name)
            scores = score_graph(graph)
            signature = build_topology_signature(graph)

            base_path = output_dir / f"{cipher_name}_{kamea.key}"
            svg_path = base_path.with_suffix(".svg")

            export_graph_with_signature_json(
                graph=graph,
                signature=signature,
                output_path=base_path.with_suffix(".json"),
            )

            export_nodes_csv(
                graph=graph,
                output_path=output_dir / f"{base_path.name}_nodes.csv",
            )

            export_edges_csv(
                graph=graph,
                output_path=output_dir / f"{base_path.name}_edges.csv",
            )

            export_scores_csv(
                scores=scores,
                output_path=output_dir / f"{base_path.name}_scores.csv",
            )

            export_graph_svg_3d(
                graph=graph,
                output_path=svg_path,
                grid_size=kamea.size,
            )

            composite_cells.append(
                CompositeImageCell(
                    image_path=svg_path,
                    row_label=cipher_name,
                    column_label=kamea.key,
                )
            )

    composite_path = output_dir / f"{safe_name(name)}_composite_overlay.svg"

    export_composite_svg(
        cells=composite_cells,
        output_path=composite_path,
        row_labels=CIPHER_ORDER,
        column_labels=KAMEA_NAMES,
        title=f"Atlas Composite Overlay: {name}",
    )

    summary = build_individual_profile_summary(name)
    interpretation = interpret_profile_summary(summary)
    report = build_profile_markdown_report(summary, interpretation)

    summary_path = output_dir / f"{safe_name(name)}_profile_summary.json"
    interpretation_path = output_dir / f"{safe_name(name)}_profile_interpretation.json"
    report_path = output_dir / f"{safe_name(name)}_codex_report.md"

    write_json(summary, summary_path)
    write_json(profile_interpretation_to_dict(interpretation), interpretation_path)
    write_markdown_report(report, report_path)

    manifest_path = write_composite_profile_manifest(name, output_dir)
    essence_paths = build_essence_profile(name, output_dir)

    print(f"\nIndividual Codex profile written to: {output_dir}")
    print(f"Composite overlay written to: {composite_path}")
    print(f"Profile summary written to: {summary_path}")
    print(f"Profile interpretation written to: {interpretation_path}")
    print(f"Codex report written to: {report_path}")
    print(f"Composite manifest written to: {manifest_path}")
    print(f"Essence graph written to: {essence_paths['json']}")
    print(f"Essence 3D topology written to: {essence_paths['svg']}")


def compare_profiles(name_a: str, name_b: str) -> None:
    """Compare two profiles across all ciphers and Kameas."""
    output_dir = (
        Path("output/console/comparisons")
        / f"{safe_name(name_a)}_vs_{safe_name(name_b)}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    cipher_results_a = run_all_ciphers(name_a)
    cipher_results_b = run_all_ciphers(name_b)

    for cipher_name in cipher_results_a:
        values_a = cipher_results_a[cipher_name]
        values_b = cipher_results_b[cipher_name]

        for kamea_name in KAMEA_NAMES:
            kamea = get_kamea(kamea_name)

            graph_a = build_graph(values_a, kamea_name)
            graph_b = build_graph(values_b, kamea_name)

            diff = compare_graphs(graph_a, graph_b)
            resonance = calculate_resonance(graph_a, graph_b)

            output_path = output_dir / f"{cipher_name}_{kamea.key}_comparison.json"

            export_comparison_json(
                graph_a=graph_a,
                graph_b=graph_b,
                diff=diff,
                resonance=resonance,
                output_path=output_path,
            )

    print(f"\nComparison written to: {output_dir}")


def build_group_overlay(names: list[str]) -> None:
    """Build group overlay profile."""
    group_name = "__".join(safe_name(name) for name in names)
    output_dir = Path("output/console/group_overlays") / group_name
    output_dir.mkdir(parents=True, exist_ok=True)

    composite_cells: list[CompositeImageCell] = []

    cipher_results_by_name = {
        name: run_all_ciphers(name)
        for name in names
    }

    cipher_names = list(next(iter(cipher_results_by_name.values())).keys())

    for cipher_name in cipher_names:
        for kamea_name in KAMEA_NAMES:
            kamea = get_kamea(kamea_name)
            graphs = []

            for name in names:
                values = cipher_results_by_name[name][cipher_name]
                graph = build_graph(values, kamea_name)
                graphs.append(graph)

            overlay_graph = overlay_graphs(graphs)
            scores = score_graph(overlay_graph)
            signature = build_topology_signature(overlay_graph)

            base_path = output_dir / f"{cipher_name}_{kamea.key}_group_overlay"
            svg_path = base_path.with_suffix(".svg")

            export_graph_with_signature_json(
                graph=overlay_graph,
                signature=signature,
                output_path=base_path.with_suffix(".json"),
            )

            export_nodes_csv(
                graph=overlay_graph,
                output_path=output_dir / f"{base_path.name}_nodes.csv",
            )

            export_edges_csv(
                graph=overlay_graph,
                output_path=output_dir / f"{base_path.name}_edges.csv",
            )

            export_scores_csv(
                scores=scores,
                output_path=output_dir / f"{base_path.name}_scores.csv",
            )

            export_graph_svg_3d(
                graph=overlay_graph,
                output_path=svg_path,
                grid_size=kamea.size,
            )

            composite_cells.append(
                CompositeImageCell(
                    image_path=svg_path,
                    row_label=cipher_name,
                    column_label=kamea.key,
                )
            )

    composite_path = output_dir / f"{group_name}_composite_overlay.svg"

    export_composite_svg(
        cells=composite_cells,
        output_path=composite_path,
        row_labels=CIPHER_ORDER,
        column_labels=KAMEA_NAMES,
        title=f"Atlas Group Composite Overlay: {', '.join(names)}",
    )

    print(f"\nGroup overlay written to: {output_dir}")
    print(f"Composite overlay written to: {composite_path}")


def save_profile(name: str) -> None:
    """Save one profile into the persistent library."""
    profile_dir = save_profile_to_library(name)
    manifest_path = write_composite_profile_manifest(name, profile_dir)
    essence_paths = build_essence_profile(name, profile_dir)

    print(f"\nSaved profile to library: {profile_dir}")
    print(f"Composite manifest written to: {manifest_path}")
    print(f"Essence graph written to: {essence_paths['json']}")
    print(f"Essence 3D topology written to: {essence_paths['svg']}")


def show_saved_profiles() -> None:
    """Print saved profiles."""
    profiles = list_saved_profiles()

    if not profiles:
        print("\nNo saved profiles found.")
        return

    print("\nSaved profiles:")
    for profile in profiles:
        print(f"- {profile}")


def show_saved_profile_summary(profile_key: str) -> None:
    """Print saved profile interpretation summary."""
    if not profile_exists(profile_key):
        print(f"\nProfile not found: {profile_key}")
        print("Use option 5 to list saved profile keys.")
        return

    interpretation = load_profile_interpretation(profile_key)

    print(f"\nProfile: {interpretation['name']}")
    print(f"Analysis count: {interpretation['analysis_count']}")

    print("\nSummary:")
    for line in interpretation["summary_lines"]:
        print(f"- {line}")

    print("\nDominant patterns:")
    for pattern, count in interpretation["dominant_patterns"].items():
        print(f"- {pattern}: {count}")

    print("\nDominant motifs:")
    for motif, count in interpretation["dominant_motifs"].items():
        print(f"- {motif}: {count}")


def build_graph(values: list[int], kamea_name: str):
    """Build graph from values and Kamea name."""
    path = project_values_to_kamea(values, kamea_name)
    return build_graph_from_kamea_path(path)


if __name__ == "__main__":
    main()