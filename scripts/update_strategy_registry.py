
"""Update Strategy Registry v3."""

from __future__ import annotations

from atlas.investment.strategy_registry import build_strategy_registry_report


def main() -> None:
    report = build_strategy_registry_report()

    print(report["success"])
    print(report["summary"])

    for row in report.get("strategies", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
