
"""Run Paper Trading Engine."""

from __future__ import annotations

from atlas.investment.paper_trading import build_paper_trading_report


def main() -> None:
    report = build_paper_trading_report()

    print(report["success"])
    print(report["text_summary"])
    print("Summary:", report["summary"])

    for row in report.get("portfolio", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
