
"""Run Alpha Backtesting Engine."""

from __future__ import annotations

import argparse

from atlas.investment.alpha.backtester import build_alpha_backtest_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-trades", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_alpha_backtest_report(min_trades=args.min_trades)

    print(report["success"])
    print(report["summary"])
    print("JSON:", report.get("json_path"))
    print("Rankings:", report.get("rankings_csv"))
    print("Trades:", report.get("trades_csv"))
    print("Markdown:", report.get("markdown_path"))

    top = (report.get("ranked_results") or [])[:5]
    for row in top:
        raw = row.get("metrics", {})
        non = row.get("non_overlapping_metrics", {})
        print(
            row.get("hypothesis_id"),
            "score=", row.get("alpha_score"),
            "raw_trades=", raw.get("trade_count"),
            "raw_avg=", raw.get("avg_return"),
            "non_trades=", non.get("trade_count"),
            "non_avg=", non.get("avg_return"),
            "non_pf=", non.get("profit_factor"),
            "concentration=", row.get("asset_concentration"),
        )


if __name__ == "__main__":
    main()
