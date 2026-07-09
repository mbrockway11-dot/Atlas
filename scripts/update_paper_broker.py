
"""Update Paper Broker v2."""

from __future__ import annotations

from atlas.investment.paper_broker import build_paper_broker_report


def main() -> None:
    report = build_paper_broker_report()

    print(report["success"])
    print(report["summary"])

    for row in report.get("new_fills", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
