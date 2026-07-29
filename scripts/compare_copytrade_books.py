"""Compare the parallel forward-paper copy-trade books side by side.

Reads every book's equity log under output/investment_forward_copytrade/<book>/
and prints a compact scoreboard: latest equity, total return, a simple daily
return-Sharpe, max drawdown, and the current book shape. This is the readout for
the A/B experiment (cap025 vs cap050) -- when enough cycles have accrued, the
higher risk-adjusted curve answers the per-coin-cap question with data instead
of a guess. Read-only; no network.

    .venv/Scripts/python.exe scripts/compare_copytrade_books.py
"""

from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean, pstdev

BASE_DIR = Path("output/investment_forward_copytrade")


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


def main() -> int:
    if not BASE_DIR.exists():
        print(f"No book directory at {BASE_DIR}.")
        return 1
    books = sorted(d.name for d in BASE_DIR.iterdir()
                   if d.is_dir() and (d / "forward_equity_log.csv").exists())
    if not books:
        print(f"No book equity logs under {BASE_DIR}/<book>/. Run --ab first.")
        return 1

    print(f"Copy-trade forward books under {BASE_DIR}:\n")
    print(f"{'book':10} {'cap':>5} {'cyc':>4} {'days':>5} {'equity':>12} "
          f"{'return':>9} {'sharpe':>8} {'maxDD':>8} {'shape':>8}")
    for name in books:
        rows = _load(BASE_DIR / name / "forward_equity_log.csv")
        if not rows:
            continue
        m = _metrics(rows)
        print(f"{name:10} {str(m['cap']):>5} {m['cycles']:>4} {m['days']:>5} "
              f"${m['equity']:>10,.0f} {m['total_return']*100:>+8.2f}% "
              f"{m['sharpe']:>+8.3f} {m['max_dd']*100:>+7.1f}% {m['shape']:>8}")

    print("\nSharpe here is per-cycle, not annualized; with only a few cycles it is "
          "not yet meaningful.\nLet the books accrue days before reading the winner.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
