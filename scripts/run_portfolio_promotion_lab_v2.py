"""Run Portfolio Promotion Lab v2."""

from __future__ import annotations

from atlas.investment.portfolio_promotion_lab_v2 import (
    build_portfolio_promotion_v2_report,
)


def main() -> None:
    report = (
        build_portfolio_promotion_v2_report()
    )

    print(report["success"])
    print(report["summary"])
    print(
        "Decision:",
        report.get("decision"),
    )
    print(
        "Baseline:",
        report.get(
            "baseline_metrics"
        ),
    )
    print(
        "Candidate:",
        report.get(
            "candidate_metrics"
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
