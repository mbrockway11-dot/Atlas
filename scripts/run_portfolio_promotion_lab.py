"""Run Portfolio Promotion Lab v1."""

from __future__ import annotations

from atlas.investment.portfolio_promotion_lab import (
    build_portfolio_promotion_report,
)


def main() -> None:
    report = (
        build_portfolio_promotion_report()
    )

    print(report["success"])
    print(report["summary"])
    print(
        "Decision:",
        report.get("decision"),
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
