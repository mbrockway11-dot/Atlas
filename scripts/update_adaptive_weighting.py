
"""Update Adaptive Weighting v3."""

from __future__ import annotations

from atlas.investment.adaptive_weighting import build_adaptive_weighting_report


def main() -> None:
    report = build_adaptive_weighting_report()

    print(report["success"])
    print(report["summary"])

    for row in report.get("rows", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
