"""Update Atlas Experiment Registry v1."""

from __future__ import annotations

from atlas.investment.experiment_registry import (
    build_experiment_registry_report,
)


def main() -> None:
    report = (
        build_experiment_registry_report()
    )

    print(report["success"])
    print(report["summary"])
    print(
        "Counts:",
        report["counts"],
    )
    print(
        "Types:",
        report[
            "experiment_type_counts"
        ],
    )
    print(
        "Statuses:",
        report["status_counts"],
    )
    print("Outputs:")

    for name, path in report[
        "outputs"
    ].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
