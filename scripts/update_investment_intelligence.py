
"""Update Atlas Investment Intelligence Layer v1."""

from __future__ import annotations

from atlas.investment.intelligence import (
    build_investment_intelligence_report,
)


def main() -> None:
    report = build_investment_intelligence_report()

    print(report["success"])
    print(report["summary"])
    print("Confidence:", report["confidence"])
    print("Health:", report["health"])
    print("Portfolio:", report["portfolio_explanation"])

    print("Recommendations:")
    for recommendation in report.get("recommendations", []):
        print("-", recommendation)

    print("Assets:")
    for row in report.get("asset_explanations", []):
        print(row)

    print("Trades:")
    for row in report.get("trade_explanations", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
