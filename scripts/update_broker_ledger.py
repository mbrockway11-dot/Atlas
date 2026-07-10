
"""Update Broker Ledger v4.1."""

from __future__ import annotations

from atlas.investment.broker_ledger import (
    build_broker_ledger_report,
)


def main() -> None:
    report = build_broker_ledger_report()

    print(report["success"])
    print(report["summary"])
    print("Cash:", report["cash"])
    print("Market value:", report["market_value"])
    print("Equity:", report["equity"])
    print("Reconciliation:", report["reconciliation"])

    for row in report.get("positions", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
