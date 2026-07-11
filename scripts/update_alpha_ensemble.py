
"""Update Alpha Ensemble v6.1."""

from __future__ import annotations

from atlas.investment.alpha_ensemble import (
    build_alpha_ensemble_report,
)


def main() -> None:
    report = build_alpha_ensemble_report()

    print(report["success"])
    print(report["summary"])
    print("Regime:", report.get("regime"))
    print("Counts:", report.get("counts"))

    print("Rankings:")
    for row in report.get("scores", []):
        print({
            "rank": row.get("ensemble_rank"),
            "asset": row.get("asset"),
            "score": row.get("ensemble_score"),
            "confidence": row.get("confidence"),
            "conviction": row.get("conviction"),
            "action": row.get("ensemble_action"),
            "sources": row.get("source_count"),
            "sector": row.get("sector"),
        })

    print("Allocations:")
    for row in report.get("allocations", []):
        print(row)

    print("Rotations:")
    for row in report.get("rotations", []):
        print(row)

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()


