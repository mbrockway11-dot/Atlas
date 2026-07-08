
"""Build Execution Planner."""

from __future__ import annotations

from atlas.investment.execution_planner import build_execution_planner_report


def main() -> None:
    report = build_execution_planner_report()

    print(report["success"])
    print(report["summary"])
    print("Decision:", report["decision"])

    for row in report.get("orders", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
