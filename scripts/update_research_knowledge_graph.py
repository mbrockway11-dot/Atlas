"""Update Atlas Research Knowledge Graph v1."""

from __future__ import annotations

from atlas.investment.research_knowledge_graph import (
    build_knowledge_graph_report,
)


def main() -> None:
    report = (
        build_knowledge_graph_report()
    )

    print(report["success"])
    print(report["summary"])
    print(
        "State hash:",
        report["state_hash"],
    )
    print(
        "Counts:",
        report["counts"],
    )
    print(
        "Node types:",
        report["node_type_counts"],
    )
    print(
        "Edge types:",
        report["edge_type_counts"],
    )
    print("Outputs:")

    for name, path in report[
        "outputs"
    ].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
