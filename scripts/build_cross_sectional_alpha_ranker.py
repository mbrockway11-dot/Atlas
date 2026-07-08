
"""Build Cross-Sectional Alpha Ranker."""

from __future__ import annotations

from atlas.investment.alpha.ranker import build_cross_sectional_alpha_ranker_report


def main() -> None:
    report = build_cross_sectional_alpha_ranker_report()

    print(report["success"])
    print(report.get("summary", report.get("error", "")))

    for row in report.get("latest_top_assets", [])[:10]:
        print(
            row.get("asset"),
            "rank=", row.get("final_rank"),
            "score=", row.get("final_alpha_score"),
            "ensemble=", row.get("ensemble_confidence"),
            "label=", row.get("final_rank_label"),
        )

    print("Outputs:", report.get("outputs"))


if __name__ == "__main__":
    main()
