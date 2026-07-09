
"""Update Position Manager v3."""

from __future__ import annotations

from atlas.investment.position_manager import build_position_manager_report


def main() -> None:
    report = build_position_manager_report()

    print(report["success"])
    print(report["summary"])
    print("Action counts:", report.get("action_counts"))

    for row in report.get("actions", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
