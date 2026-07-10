
"""Build Market Features v2 from Market Universe v1."""

from __future__ import annotations

from atlas.investment.alpha.market_features import (
    build_market_feature_report,
)


def main() -> None:
    report = build_market_feature_report()

    print(report["success"])
    print(report["summary"])
    print("Asset rows:", report.get("asset_feature_rows"))
    print("Market rows:", report.get("market_feature_rows"))
    print("History rows:", report.get("history_rows"))
    print("Assets:", report.get("assets"))
    print("Aggregate:", report.get("market_aggregate"))

    print("Rankings:")
    for row in report.get("latest_features", []):
        print({
            "rank": row.get("cross_sectional_rank"),
            "asset": row.get("asset"),
            "score": row.get("cross_sectional_score"),
            "return_30d": row.get("return_30d"),
            "momentum_30d": row.get("momentum_30d"),
            "volatility_30d": row.get(
                "volatility_30d"
            ),
            "trend_state": row.get("trend_state"),
        })

    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
