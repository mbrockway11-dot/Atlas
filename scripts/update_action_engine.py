
"""Update Action Engine."""

from __future__ import annotations

from atlas.investment.action_engine import build_action_engine_report


def main() -> None:
    report = build_action_engine_report()

    print(report["success"])
    print(report["summary"])

    for row in report.get("actions", []):
        print(row)

    print("Outputs:", report.get("outputs"))


if __name__ == "__main__":
    main()
