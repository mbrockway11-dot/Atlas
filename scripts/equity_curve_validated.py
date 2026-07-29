"""Paper equity curve for the validated dr + defensive ensemble, 2021-2026.

Read-only. Builds a daily, fully-invested, equal-weight-across-active-positions
equity curve from the two promoted engines' non-overlapping trades over the full
backfilled history (including the 2021-2022 bear), net of a round-trip cost. Each
trade is spread across its holding period; each day the portfolio return is the
mean return of the positions active that day (across both engines). Reports total
return, CAGR, max drawdown, and a Sharpe-like ratio, and writes the daily series.

This is a backtest equity curve, not a live forward run -- the honest artifact
for "how would the validated config have done", spanning both regimes.

    .venv/Scripts/python.exe scripts/equity_curve_validated.py --round-trip-bps 20
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
from collections import defaultdict
from pathlib import Path

TRADES = Path(
    "output/investment_alpha_engines/historical_alpha_engine_non_overlapping_trades.csv"
)
ENGINES = ("drawdown_recovery_v1", "defensive_risk_off_v1")
OUT = Path("output/investment_alpha_portfolio/validated_equity_curve.csv")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trades", default=str(TRADES))
    parser.add_argument("--round-trip-bps", type=float, default=20.0)
    parser.add_argument(
        "--fraction",
        type=float,
        default=0.02,
        help="Capital risked per trade (fixed-fractional; realized at exit).",
    )
    args = parser.parse_args(argv)
    cost = args.round_trip_bps / 10000.0
    f = args.fraction

    rows = [
        r
        for r in csv.DictReader(open(args.trades, encoding="utf-8"))
        if r["engine_id"] in ENGINES
    ]

    # Fixed-fractional compounding: each trade realizes its net return on a fixed
    # fraction of equity at its EXIT date, applied in exit order. This is the
    # correct way to turn discrete trades into a portfolio curve -- it avoids the
    # volatility drag that a naive daily equal-weight rebalance injects.
    realized: list[tuple[dt.date, float]] = []
    for r in rows:
        exitd = dt.datetime.fromisoformat(r["exit_timestamp"]).date()
        net = float(r["strategy_return"]) - cost
        realized.append((exitd, f * net))
    realized.sort(key=lambda x: x[0])

    start = dt.datetime.fromisoformat(rows[0]["date"]).date()
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    trade_rets: list[float] = []
    daily: dict[dt.date, float] = {}
    for exitd, chg in realized:
        equity *= 1.0 + chg
        peak = max(peak, equity)
        max_dd = min(max_dd, equity / peak - 1.0)
        trade_rets.append(chg)
        daily[exitd] = equity

    end = realized[-1][0]
    # Forward-fill a daily curve for charting.
    curve: list[tuple[dt.date, float, float]] = []
    eq = 1.0
    d = start
    while d <= end:
        if d in daily:
            eq = daily[d]
        curve.append((d, round(eq, 6), 0.0))
        d += dt.timedelta(days=1)

    years = (end - start).days / 365.25
    total_return = equity - 1.0
    cagr = (equity ** (1.0 / years) - 1.0) if years > 0 else 0.0
    mean_t = sum(trade_rets) / len(trade_rets)
    var_t = sum((x - mean_t) ** 2 for x in trade_rets) / max(1, len(trade_rets) - 1)
    std_t = math.sqrt(var_t)
    trades_per_year = len(trade_rets) / years if years > 0 else 0.0
    sharpe = (mean_t / std_t * math.sqrt(trades_per_year)) if std_t > 0 else 0.0
    invested_days = len(curve)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "equity", "daily_return"])
        w.writerows(curve)

    print(f"Validated config (drawdown_recovery + defensive_risk_off), equal-weight")
    print(f"  span:          {start} .. {end}  ({years:.1f} yr)")
    print(f"  round-trip cost: {args.round_trip_bps:.0f}bps   invested {invested_days}/{len(curve)} days")
    print(f"  total return:  {total_return * 100:+.1f}%   (final equity {equity:.2f}x)")
    print(f"  CAGR:          {cagr * 100:+.1f}%")
    print(f"  max drawdown:  {max_dd * 100:.1f}%")
    print(f"  Sharpe-like:   {sharpe:.2f}")
    # Equity at a few checkpoints incl. bear.
    bench = {}
    for d0, eq, _ in curve:
        bench[d0.isoformat()[:7]] = eq
    print("  equity by month (sampled):")
    keys = sorted(bench)
    for m in keys[::6]:
        print(f"    {m}: {bench[m]:.2f}x")
    print(f"  wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
