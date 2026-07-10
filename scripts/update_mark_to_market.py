
"""Update Mark-to-Market v4."""

from __future__ import annotations

from atlas.investment.mark_to_market import (
    build_mark_to_market_report,
)


def main() -> None:
    report = build_mark_to_market_report()

    print(report["success"])
    print(report["summary"])

    if report.get("equity_snapshot"):
        print("Equity:", report["equity_snapshot"])

    for row in report.get("positions", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
