
"""Simulate latest execution plan."""

from __future__ import annotations

from atlas.investment.execution_simulator import build_execution_simulator_report


def main() -> None:
    report = build_execution_simulator_report()

    print(report["success"])
    print(report["text_summary"])
    print("Summary:", report["summary"])

    for row in report.get("fills", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
