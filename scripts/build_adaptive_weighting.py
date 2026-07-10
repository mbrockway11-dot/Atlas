
"""Build Adaptive Weighting."""

from __future__ import annotations

from atlas.investment.adaptive_weighting import build_adaptive_weighting_report


def main() -> None:
    report = build_adaptive_weighting_report()

    print(report["success"])
    print(report["summary"])

    for family, weight in report.get("family_weights", {}).items():
        print(family, weight)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
