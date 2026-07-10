
"""Update Alpha Ensemble v4."""

from __future__ import annotations

from atlas.investment.alpha_ensemble import build_alpha_ensemble_report


def main() -> None:
    report = build_alpha_ensemble_report()

    print(report["success"])
    print(report["summary"])

    for row in report.get("scores", []):
        print(row)

    print("Allocations:")
    for row in report.get("allocations", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
