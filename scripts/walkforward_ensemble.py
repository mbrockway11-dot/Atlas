"""Walk-forward the ensemble of the walk-forward-surviving engines.

Read-only. The single-engine walk-forward showed three engines survive out of
sample (drawdown_recovery, volatility_compression, trend_continuation). An
auto-trader would run them together, so this tests the blend: does combining the
three independent survivors keep the return while cutting the per-window
variance and worst case -- the only reason to ensemble at all?

Three blends are compared against drawdown_recovery solo, all net of a round-trip
cost, over the same consecutive windows:
  - equal-per-trade:  pool every survivor trade, weight each equally
  - equal-per-engine: average the engines' per-window means (engine-balanced)
  - conviction:       weight each trade by its emitted conviction

Same ~2-year, single-regime data caveat as the per-engine run: this measures
diversification benefit, not bear-market survival.

    .venv/Scripts/python.exe scripts/walkforward_ensemble.py --window-days 120
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
SURVIVORS = ("drawdown_recovery_v1", "volatility_compression_v1", "trend_continuation_v1")


def _summ(name: str, per_window: list[float]) -> None:
    if not per_window:
        print(f"  {name:22}: no windows")
        return
    pos = sum(1 for m in per_window if m > 0)
    stdev = statistics.pstdev(per_window) if len(per_window) > 1 else 0.0
    print(
        f"  {name:22}: {pos}/{len(per_window)} +windows  "
        f"mean {statistics.fmean(per_window) * 100:+.2f}%  "
        f"median {statistics.median(per_window) * 100:+.2f}%  "
        f"worst {min(per_window) * 100:+.2f}%  "
        f"stdev {stdev * 100:.2f}%  "
        f"[{'  '.join(f'{m * 100:+.1f}' for m in per_window)}]"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trades", default=str(TRADES))
    parser.add_argument("--window-days", type=int, default=120)
    parser.add_argument("--round-trip-bps", type=float, default=20.0)
    parser.add_argument("--min-window-trades", type=int, default=8)
    parser.add_argument(
        "--engines",
        default=",".join(SURVIVORS),
        help="Comma-separated engine_ids to ensemble.",
    )
    args = parser.parse_args(argv)
    members = tuple(e.strip() for e in args.engines.split(",") if e.strip())

    rows = [
        r
        for r in csv.DictReader(open(args.trades, encoding="utf-8"))
        if r["engine_id"] in members
    ]
    cost = args.round_trip_bps / 10000.0
    for r in rows:
        r["_date"] = dt.datetime.fromisoformat(r["date"]).date()
        r["_net"] = float(r["strategy_return"]) - cost
        try:
            r["_conv"] = max(0.0, float(r["conviction"]))
        except (ValueError, KeyError):
            r["_conv"] = 1.0

    start = min(r["_date"] for r in rows)
    end = max(r["_date"] for r in rows)
    step = dt.timedelta(days=args.window_days)
    bounds = []
    d = start
    while d <= end:
        bounds.append((d, d + step))
        d += step

    def window_of(date):
        for i, (lo, hi) in enumerate(bounds):
            if lo <= date < hi:
                return i
        return None

    # Collect per-window trades, and per-window per-engine trades.
    pool: dict[int, list[dict]] = defaultdict(list)
    per_eng: dict[int, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        w = window_of(r["_date"])
        if w is None:
            continue
        pool[w].append(r)
        per_eng[w][r["engine_id"]].append(r["_net"])

    dr_solo, ens_trade, ens_engine, ens_conv = [], [], [], []
    for i in range(len(bounds)):
        trades = pool.get(i, [])
        if len(trades) < args.min_window_trades:
            continue
        # equal-per-trade
        ens_trade.append(statistics.fmean([t["_net"] for t in trades]))
        # conviction-weighted
        wsum = sum(t["_conv"] for t in trades) or 1.0
        ens_conv.append(sum(t["_net"] * t["_conv"] for t in trades) / wsum)
        # equal-per-engine (engines present with any trades that window)
        eng_means = [
            statistics.fmean(v) for v in per_eng[i].values() if v
        ]
        if eng_means:
            ens_engine.append(statistics.fmean(eng_means))
        # drawdown_recovery solo
        dr = per_eng[i].get("drawdown_recovery_v1", [])
        if len(dr) >= args.min_window_trades:
            dr_solo.append(statistics.fmean(dr))

    print(
        f"Survivor ensemble walk-forward | {len(rows)} trades | "
        f"{start}..{end} | {len(bounds)} windows of {args.window_days}d | "
        f"cost {args.round_trip_bps:.0f}bps"
    )
    print("\nPer-window mean net return (time order):")
    _summ("drawdown_recovery SOLO", dr_solo)
    _summ("ENSEMBLE equal-trade", ens_trade)
    _summ("ENSEMBLE equal-engine", ens_engine)
    _summ("ENSEMBLE conviction", ens_conv)
    print(
        "\nReading: the ensemble earns its keep if it holds the mean while "
        "raising 'worst' and lowering 'stdev' vs drawdown_recovery solo."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
