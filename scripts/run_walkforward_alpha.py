
"""Run Walk-Forward Alpha Engine."""

from __future__ import annotations

import argparse

from atlas.investment.alpha.walkforward import build_walkforward_alpha_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-days", type=int, default=730)
    parser.add_argument("--test-days", type=int, default=180)
    parser.add_argument("--step-days", type=int, default=180)
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument("--min-train-trades", type=int, default=30)
    parser.add_argument("--exposure", type=float, default=0.10)
    parser.add_argument("--drawdown-control", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    report = build_walkforward_alpha_report(
        train_days=args.train_days,
        test_days=args.test_days,
        step_days=args.step_days,
        top_n=args.top_n,
        min_train_trades=args.min_train_trades,
        exposure=args.exposure,
        drawdown_control=args.drawdown_control,
    )

    print(report["success"])
    print(report.get("summary", report.get("error", "")))
    print("Splits:", report.get("split_count"))
    print("Stability:", report.get("stability_score"))
    print("Aggregate test:", report.get("aggregate_test"))


if __name__ == "__main__":
    main()
