
"""Update Action Engine v3."""

from __future__ import annotations

from atlas.investment.action_engine import build_action_engine_report


def main() -> None:
    report = build_action_engine_report()

    print(report["success"])
    print(report["summary"])
    print("Action counts:", report.get("action_counts"))

    for row in report.get("actions", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
