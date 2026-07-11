"""Run Portfolio Optimizer v2."""

from __future__ import annotations

from atlas.investment.portfolio_optimizer import (
    build_portfolio_optimizer_report,
)


def main() -> None:
    report = (
        build_portfolio_optimizer_report()
    )

    print(report["success"])
    print(report["summary"])
    print(
        "Controls:",
        report.get("controls"),
    )
    print(
        "Risk:",
        report.get("risk"),
    )
    print(
        "Diagnostics:",
        report.get("diagnostics"),
    )

    print("Portfolio:")

    for row in report.get(
        "portfolio",
        [],
    ):
        print({
            "asset": row.get("asset"),
            "weight": row.get(
                "target_weight"
            ),
            "score": row.get(
                "optimizer_score"
            ),
            "risk_contribution": row.get(
                "risk_contribution"
            ),
        })

    print("Outputs:")

    for name, path in report.get(
        "outputs",
        {},
    ).items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
