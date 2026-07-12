"""Run Atlas Research Experiment Execution Lab v1."""

from __future__ import annotations

from atlas.investment.research_experiment_execution import (
    build_research_experiment_execution_report,
)


def main() -> None:
    report = (
        build_research_experiment_execution_report()
    )

    print(report["success"])
    print(report["summary"])
    print(
        "State hash:",
        report["state_hash"],
    )
    print(
        "Observation source:",
        report[
            "observation_source_path"
        ],
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
