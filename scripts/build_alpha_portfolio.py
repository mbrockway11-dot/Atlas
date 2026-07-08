
"""Build Alpha Portfolio."""

from __future__ import annotations

from atlas.investment.alpha.portfolio import build_alpha_portfolio_report


def main() -> None:
    report = build_alpha_portfolio_report()

    print(report["success"])
    print(report.get("summary", report.get("error", "")))

    for row in report.get("portfolio", []):
        print(
            row.get("asset"),
            "weight=", row.get("target_weight"),
            "rank=", row.get("rank"),
            "label=", row.get("rank_label"),
        )

    print("Risk:", report.get("risk"))
    print("Outputs:", report.get("outputs"))


if __name__ == "__main__":
    main()
