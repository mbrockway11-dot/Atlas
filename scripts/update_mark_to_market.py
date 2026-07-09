
"""Update Mark-to-Market v2."""

from __future__ import annotations

from atlas.investment.mark_to_market import build_mark_to_market_report


def main() -> None:
    report = build_mark_to_market_report()

    print(report["success"])
    print(report["summary"])
    print("Equity:", report["equity_snapshot"])

    for row in report.get("positions", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
