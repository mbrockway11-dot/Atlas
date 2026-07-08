
"""Build Broker Interface report."""

from __future__ import annotations

from atlas.investment.broker import build_broker_interface_report


def main() -> None:
    report = build_broker_interface_report()

    print(report["success"])
    print(report["summary"])
    for order in report.get("orders", []):
        print(order)
    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
