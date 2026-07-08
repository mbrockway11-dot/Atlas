
"""Update portfolio performance."""

from __future__ import annotations

from atlas.investment.performance import build_performance_report


def main() -> None:
    report = build_performance_report()

    print(report["success"])
    print(report["summary"])
    print("PnL:", report["pnl"])
    print("Positions:", report["positions"])

    for row in report.get("attribution", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
