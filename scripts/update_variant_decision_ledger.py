"""Synchronize Manual Variant Decision Ledger v1."""

from __future__ import annotations

from atlas.investment.variant_decisions import (
    build_variant_decision_report,
)


def main() -> None:
    report = (
        build_variant_decision_report()
    )

    print(report["success"])
    print(report["summary"])

    print(
        "Decision counts:",
        report.get(
            "decision_counts"
        ),
    )

    print(
        "Counts:",
        report.get("counts"),
    )

    print("Outputs:")

    for name, path in report.get(
        "outputs",
        {},
    ).items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
