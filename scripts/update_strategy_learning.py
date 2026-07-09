
"""Update Learning Engine v3."""

from __future__ import annotations

from atlas.investment.learning import build_learning_report


def main() -> None:
    report = build_learning_report()

    print(report["success"])
    print(report["summary"])
    print("Regime:", report["learning_regime"])
    print("Recommendations:")

    for rec in report.get("recommendations", []):
        print("-", rec)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
