"""Compare the parallel forward-paper copy-trade books side by side.

Reads every book's equity log under output/investment_forward_copytrade/<book>/
and prints a compact scoreboard (latest equity, total return, per-cycle Sharpe,
max drawdown, shape), then the part that actually answers the questions: the
time-aligned PAIRED spreads. Because the copy books share a roster and marks,
their curves are ~95% correlated, so comparing two Sharpes by eye is hopeless --
the signal lives in the difference series. This computes:

  * cap050 - cap025: does loosening the per-coin cap help? (the A/B)
  * each copy book - btc / - ewmajors: does copying beat holding beta?

each as a mean per-cycle spread with a paired t-stat, so a verdict comes with a
confidence, not a vibe. Read-only; no network.

    .venv/Scripts/python.exe scripts/compare_copytrade_books.py
"""

from __future__ import annotations

import csv
from math import sqrt
from pathlib import Path
from statistics import mean, pstdev

BASE_DIR = Path("output/investment_forward_copytrade")
COPY_BOOKS = ("cap025", "cap050")
BENCHMARKS = ("btc", "ewmajors")


def _load(equity_log: Path) -> list[dict]:
    if not equity_log.exists():
        return []
    return list(csv.DictReader(equity_log.open(encoding="utf-8")))


def _metrics(rows: list[dict]) -> dict:
    equities = [float(r["equity"]) for r in rows]
    start, last = equities[0], equities[-1]
    peak, max_dd = equities[0], 0.0
    for equity in equities:
        peak = max(peak, equity)
        max_dd = min(max_dd, equity / peak - 1.0)
    rets = [equities[i] / equities[i - 1] - 1.0 for i in range(1, len(equities))]
    sharpe = (mean(rets) / pstdev(rets)) if len(rets) > 1 and pstdev(rets) > 0 else 0.0
    last_row = rows[-1]
    return {
        "cycles": len(rows),
        "days": len({r["timestamp"][:10] for r in rows}),
        "equity": last,
        "total_return": last / start - 1.0,
        "sharpe": sharpe,
        "max_dd": max_dd,
        "shape": f"{last_row.get('n_long','?')}L/{last_row.get('n_short','?')}S",
        "cap": last_row.get("coin_cap", "?"),
    }


def _equity_by_time(rows: list[dict]) -> dict[str, float]:
    return {r["timestamp"]: float(r["equity"]) for r in rows}


def _paired_spread(rows_a: list[dict], rows_b: list[dict]) -> dict | None:
    """Per-cycle return spread (a - b) over the timestamps both books share."""
    a, b = _equity_by_time(rows_a), _equity_by_time(rows_b)
    times = sorted(set(a) & set(b))
    if len(times) < 2:
        return None
    spreads = []
    for prev, cur in zip(times, times[1:]):
        ret_a = a[cur] / a[prev] - 1.0
        ret_b = b[cur] / b[prev] - 1.0
        spreads.append(ret_a - ret_b)
    n = len(spreads)
    mu, sd = mean(spreads), (pstdev(spreads) if n > 1 else 0.0)
    t = (mu / (sd / sqrt(n))) if sd > 0 else 0.0
    return {"n": n, "mean_bps": mu * 1e4, "t": t}


def _print_pair(label: str, stat: dict | None) -> None:
    if stat is None:
        print(f"  {label:22} (needs >= 2 shared cycles)")
        return
    verdict = "" if abs(stat["t"]) < 2.0 else "  <-- |t|>2"
    print(f"  {label:22} {stat['mean_bps']:>+8.2f} bps/cycle   "
          f"t={stat['t']:>+5.2f}  (n={stat['n']}){verdict}")


def main() -> int:
    if not BASE_DIR.exists():
        print(f"No book directory at {BASE_DIR}.")
        return 1
    books = sorted(d.name for d in BASE_DIR.iterdir()
                   if d.is_dir() and (d / "forward_equity_log.csv").exists())
    if not books:
        print(f"No book equity logs under {BASE_DIR}/<book>/. Run --ab first.")
        return 1

    loaded = {name: _load(BASE_DIR / name / "forward_equity_log.csv") for name in books}

    print(f"Copy-trade forward books under {BASE_DIR}:\n")
    print(f"{'book':10} {'cap':>5} {'cyc':>4} {'days':>5} {'equity':>12} "
          f"{'return':>9} {'sharpe':>8} {'maxDD':>8} {'shape':>8}")
    for name in books:
        if not loaded[name]:
            continue
        m = _metrics(loaded[name])
        print(f"{name:10} {str(m['cap']):>5} {m['cycles']:>4} {m['days']:>5} "
              f"${m['equity']:>10,.0f} {m['total_return']*100:>+8.2f}% "
              f"{m['sharpe']:>+8.3f} {m['max_dd']*100:>+7.1f}% {m['shape']:>8}")

    print("\nPaired spreads (time-aligned per-cycle return difference, paired t):")
    if all(b in loaded for b in COPY_BOOKS):
        _print_pair("cap050 - cap025", _paired_spread(loaded["cap050"], loaded["cap025"]))
    for copy in COPY_BOOKS:
        for bench in BENCHMARKS:
            if copy in loaded and bench in loaded:
                _print_pair(f"{copy} - {bench}", _paired_spread(loaded[copy], loaded[bench]))

    print("\nA copy book earns its keep only if it beats the benchmark (positive, |t|>2).")
    print("Per-cycle Sharpe/t are not annualized and mean little until many cycles accrue.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
