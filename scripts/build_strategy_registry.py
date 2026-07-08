
"""Build Strategy Registry."""

from __future__ import annotations

from atlas.investment.strategy_registry import build_strategy_registry_report


def main() -> None:
    report = build_strategy_registry_report()

    print(report["success"])
    print(report["text_summary"])
    print(report["summary"])

    for row in report.get("signals", []):
        print(row)

    print("Outputs:")
    print(" - output/investment_strategy_registry/strategy_registry_signals.csv")
    print(" - output/investment_strategy_registry/strategy_registry_report.json")
    print(" - output/investment_strategy_registry/strategy_registry_report.md")


if __name__ == "__main__":
    main()
