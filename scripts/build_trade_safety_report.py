
"""Build Trade Safety Governor report."""

from __future__ import annotations

from atlas.investment.safety import build_trade_safety_report


def main() -> None:
    report = build_trade_safety_report()

    print(report["success"])
    print(report["summary"])
    for check in report.get("checks", []):
        print(check)
    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
