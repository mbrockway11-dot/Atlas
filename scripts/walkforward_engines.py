"""Per-engine walk-forward: is the top alpha engine robust across time, net of fees?

Read-only. The 7 alpha engines are rule-based with FIXED parameters, so there is
no fitting to overfit -- the honest out-of-sample question is TEMPORAL: does an
engine make money in every rolling window, or was it carried by one era? This
splits the on-disk non-overlapping engine trades into consecutive windows and,
per engine, reports each window's mean per-trade return net of a round-trip
trading cost, plus how many windows were positive.

The engine ranking on disk was computed over the whole span at once; this checks
whether the winner (drawdown_recovery_v1) survives period-by-period. Trades span
only ~2 years, so this is a limited check -- stated, not hidden.

    .venv/Scripts/python.exe scripts/walkforward_engines.py --window-days 120 --round-trip-bps 20
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import statistics
from collections import defaultdict
from pathlib import Path

TRADES = Path(
    "output/investment_alpha_engines/historical_alpha_engine_non_overlapping_trades.csv"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trades", default=str(TRADES))
    parser.add_argument("--window-days", type=int, default=120)
    parser.add_argument("--round-trip-bps", type=float, default=20.0)
    parser.add_argument("--min-window-trades", type=int, default=8)
    args = parser.parse_args(argv)

    rows = list(csv.DictReader(open(args.trades, encoding="utf-8")))
    cost = args.round_trip_bps / 10000.0
    for r in rows:
        r["_date"] = dt.datetime.fromisoformat(r["date"]).date()
        r["_net"] = float(r["strategy_return"]) - cost

    start = min(r["_date"] for r in rows)
    end = max(r["_date"] for r in rows)
    step = dt.timedelta(days=args.window_days)
    # Build consecutive window boundaries.
    bounds = []
    d = start
    while d <= end:
        bounds.append((d, d + step))
        d += step
    print(
        f"Trades: {len(rows)} | span {start}..{end} | "
        f"{len(bounds)} windows of {args.window_days}d | round-trip cost "
        f"{args.round_trip_bps:.0f}bps"
    )

    # engine -> window_index -> [net returns]
    by_engine: dict[str, dict[int, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for r in rows:
        for i, (lo, hi) in enumerate(bounds):
            if lo <= r["_date"] < hi:
                by_engine[r["engine_id"]][i].append(r["_net"])
                break

    order = [
        "defensive_risk_off_v1", "drawdown_recovery_v1", "trend_continuation_v1",
        "volatility_compression_v1", "volatility_expansion_v1",
        "cross_sectional_momentum_v1", "market_breadth_v1", "mean_reversion_v1",
    ]
    print(
        f"\n{'engine':30} {'trades':>6} {'wins':>4} {'+wins/total':>11} "
        f"{'medWinRet':>9} {'worstWin':>9} {'meanNet/trade':>13}  per-window mean net %"
    )
    print("-" * 120)
    for eng in order:
        wins = by_engine.get(eng, {})
        window_means = []
        per_window_display = []
        total_trades = 0
        for i in range(len(bounds)):
            vals = wins.get(i, [])
            total_trades += len(vals)
            if len(vals) >= args.min_window_trades:
                m = statistics.fmean(vals)
                window_means.append(m)
                per_window_display.append(f"{m * 100:+.1f}")
            else:
                per_window_display.append(f"({len(vals)})")
        if not window_means:
            print(f"{eng:30} {total_trades:>6}   (too few trades per window)")
            continue
        pos = sum(1 for m in window_means if m > 0)
        all_net = [v for vals in wins.values() for v in vals]
        tag = "  <= TOP-RANKED" if eng == "drawdown_recovery_v1" else ""
        print(
            f"{eng:30} {total_trades:>6} {pos:>4} {pos:>5}/{len(window_means):<5} "
            f"{statistics.median(window_means) * 100:>+8.1f}% "
            f"{min(window_means) * 100:>+8.1f}% "
            f"{statistics.fmean(all_net) * 100:>+12.2f}%   "
            f"[{'  '.join(per_window_display)}]{tag}"
        )

    print(
        "\nReading: '+wins/total' = windows with positive net mean / windows with "
        "enough trades.\nPer-window list is mean net return % per window in time "
        "order; (n) = too few trades that window.\nA robust engine is positive in "
        "MOST windows, not carried by one."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
