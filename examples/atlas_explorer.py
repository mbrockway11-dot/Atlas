"""Atlas Explorer.

A lightweight text-based explorer for saved Atlas profiles.
"""

from atlas.library.profile_library import (
    list_saved_profiles,
    load_profile_interpretation,
    profile_exists,
    save_profile_to_library,
)
from atlas.resonance.resonance import calculate_resonance
from atlas.ciphers import run_all_ciphers
from atlas.kamea.projection import project_values_to_kamea
from atlas.topology.graph_builder import build_graph_from_kamea_path


KAMEA_NAMES = [
    "saturn",
    "jupiter",
    "mars",
    "sun",
    "venus",
    "mercury",
    "moon",
]


def main() -> None:
    """Run Atlas Explorer."""
    while True:
        print_header()

        choice = input(
            "Choose:\n"
            "1) Build and save profile\n"
            "2) List saved profiles\n"
            "3) Open profile summary\n"
            "4) Compare saved profiles\n"
            "5) Exit\n"
            "> "
        ).strip()

        if choice == "1":
            name = input("Enter full name: ").strip()
            if name:
                build_and_save_profile(name)

        elif choice == "2":
            list_profiles()

        elif choice == "3":
            profile_key = input("Enter profile key: ").strip()
            if profile_key:
                open_profile_summary(profile_key)

        elif choice == "4":
            profile_a = input("Enter first profile key: ").strip()
            profile_b = input("Enter second profile key: ").strip()
            if profile_a and profile_b:
                compare_saved_profiles(profile_a, profile_b)

        elif choice == "5":
            print("Exiting Atlas Explorer.")
            break

        else:
            print("Invalid choice.")

        input("\nPress Enter to continue...")


def print_header() -> None:
    """Print Explorer header."""
    print("\n" + "=" * 60)
    print("ATLAS EXPLORER")
    print("Saved Profile Browser")
    print("=" * 60)


def build_and_save_profile(name: str) -> None:
    """Build and save a profile to the persistent library."""
    profile_dir = save_profile_to_library(name)

    print("\nProfile saved.")
    print(f"Location: {profile_dir}")


def list_profiles() -> None:
    """List saved profiles."""
    profiles = list_saved_profiles()

    if not profiles:
        print("\nNo profiles saved yet.")
        return

    print("\nSaved profiles:")
    for index, profile in enumerate(profiles, start=1):
        print(f"{index}) {profile}")


def open_profile_summary(profile_key: str) -> None:
    """Open a saved profile summary."""
    if not profile_exists(profile_key):
        print(f"\nProfile not found: {profile_key}")
        print("Use option 2 to list available profile keys.")
        return

    interpretation = load_profile_interpretation(profile_key)

    print("\n" + "-" * 60)
    print(f"Profile: {interpretation['name']}")
    print(f"Analyses: {interpretation['analysis_count']}")
    print("-" * 60)

    print("\nSummary:")
    for line in interpretation["summary_lines"]:
        print(f"- {line}")

    print("\nDominant Patterns:")
    for pattern, count in interpretation["dominant_patterns"].items():
        print(f"- {pattern}: {count}")

    print("\nDominant Motifs:")
    for motif, count in interpretation["dominant_motifs"].items():
        print(f"- {motif}: {count}")

    print("\nStrongest Driver:")
    print_score_block(interpretation["strongest_driver"])

    print("\nStrongest Amplifier:")
    print_score_block(interpretation["strongest_amplifier"])

    print("\nStrongest Regulator:")
    print_score_block(interpretation["strongest_regulator"])


def compare_saved_profiles(profile_a: str, profile_b: str) -> None:
    """Compare two saved profile keys by rebuilding their graph resonance."""
    if not profile_exists(profile_a):
        print(f"\nProfile not found: {profile_a}")
        return

    if not profile_exists(profile_b):
        print(f"\nProfile not found: {profile_b}")
        return

    interpretation_a = load_profile_interpretation(profile_a)
    interpretation_b = load_profile_interpretation(profile_b)

    name_a = interpretation_a["name"]
    name_b = interpretation_b["name"]

    print("\n" + "-" * 60)
    print(f"Comparing: {name_a}  ↔  {name_b}")
    print("-" * 60)

    results = build_pairwise_resonance_rows(name_a, name_b)

    overall_average = sum(row["overall"] for row in results) / len(results)
    best = max(results, key=lambda row: row["overall"])
    weakest = min(results, key=lambda row: row["overall"])

    print(f"\nAverage resonance: {overall_average:.4f}")

    print("\nStrongest resonance:")
    print(
        f"- {best['planet']} / {best['cipher']}: "
        f"{best['overall']:.4f}"
    )

    print("\nWeakest resonance:")
    print(
        f"- {weakest['planet']} / {weakest['cipher']}: "
        f"{weakest['overall']:.4f}"
    )

    print("\nTop resonance rows:")
    for row in sorted(results, key=lambda item: item["overall"], reverse=True)[:5]:
        print(
            f"- {row['planet']} / {row['cipher']}: "
            f"overall={row['overall']:.4f}, "
            f"node={row['node_similarity']:.4f}, "
            f"edge={row['edge_similarity']:.4f}, "
            f"vector={row['vector_similarity']:.4f}, "
            f"alignment={row['alignment_similarity']:.4f}"
        )


def build_pairwise_resonance_rows(name_a: str, name_b: str) -> list[dict]:
    """Build all 21 resonance rows for two names."""
    cipher_results_a = run_all_ciphers(name_a)
    cipher_results_b = run_all_ciphers(name_b)

    rows = []

    for cipher_name in cipher_results_a:
        values_a = cipher_results_a[cipher_name]
        values_b = cipher_results_b[cipher_name]

        for kamea_name in KAMEA_NAMES:
            graph_a = build_graph(values_a, kamea_name)
            graph_b = build_graph(values_b, kamea_name)

            resonance = calculate_resonance(graph_a, graph_b)

            rows.append(
                {
                    "cipher": cipher_name,
                    "planet": kamea_name,
                    "overall": resonance.overall,
                    "node_similarity": resonance.node_similarity,
                    "edge_similarity": resonance.edge_similarity,
                    "node_weight_similarity": resonance.node_weight_similarity,
                    "edge_weight_similarity": resonance.edge_weight_similarity,
                    "vector_similarity": resonance.vector_similarity,
                    "alignment_similarity": resonance.alignment_similarity,
                }
            )

    return rows


def build_graph(values: list[int], kamea_name: str):
    """Build graph from values and Kamea name."""
    path = project_values_to_kamea(values, kamea_name)
    return build_graph_from_kamea_path(path)


def print_score_block(score_data: dict) -> None:
    """Print strongest score block."""
    print(f"- Planet: {score_data['planet']}")
    print(f"- Cipher: {score_data['cipher']}")
    print(f"- Score: {score_data['score']:.4f}")
    print(f"- Pattern: {score_data['dominant_pattern']}")
    print(f"- Motif: {score_data['dominant_motif']}")


if __name__ == "__main__":
    main()