
"""Update Rebalancing Engine."""

from __future__ import annotations

from atlas.investment.rebalance import build_rebalance_report


def main() -> None:
    report = build_rebalance_report()

    print(report["success"])
    print(report["summary"])
    print("Turnover:", report["total_turnover"])

    for row in report.get("orders", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
