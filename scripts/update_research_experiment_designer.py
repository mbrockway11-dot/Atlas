"""Update Atlas Research Experiment Designer v1."""

from __future__ import annotations

from atlas.investment.research_experiment_designer import (
    build_research_experiment_designer_report,
)


def main() -> None:
    report = (
        build_research_experiment_designer_report()
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
    print("Outputs:")

    for name, path in report[
        "outputs"
    ].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
