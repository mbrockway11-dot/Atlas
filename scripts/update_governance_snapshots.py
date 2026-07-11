"""Run Historical Governance Snapshots v1."""

from __future__ import annotations

from atlas.investment.governance_snapshots import (
    build_governance_snapshots_report,
)


def main() -> None:
    report = (
        build_governance_snapshots_report()
    )

    print(report["success"])
    print(report["summary"])
    print(
        "Coverage:",
        report.get("coverage"),
    )
    print(
        "Eligible engines:",
        report.get(
            "eligible_engine_count"
        ),
    )

    print("Outputs:")

    for name, path in report.get(
        "outputs",
        {},
    ).items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
