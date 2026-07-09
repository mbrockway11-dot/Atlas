
"""Update Risk Engine v2."""

from __future__ import annotations

from atlas.investment.risk_engine import build_risk_engine_report


def main() -> None:
    report = build_risk_engine_report()

    print(report["success"])
    print(report["summary"])
    print("Aggregate:", report["aggregate"])

    for block in report.get("risk_blocks", []):
        print(block)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
