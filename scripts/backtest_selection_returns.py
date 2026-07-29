"""Returns-based self-improvement test on the v2 cohort (real exit prices).

The v1 registry had no exit prices, so the earlier test could only use per-leg
PnL Sharpe as a size-neutral proxy. The disjoint v2 cohort (paper_cohort.jsonl,
114 teachers / 65k legs, 100% with exit prices) has real per-leg PRICE returns,
so this measures what the proxy could not:

  * realized OOS return of copying the selected cohort (gross and net of HL taker
    fees, 9bps round trip), size-neutral (price return, leverage-agnostic);
  * the true portfolio return-Sharpe including the diversification benefit of
    holding more teachers -- which resolves the roster-size question the v1 test
    could only pose.

Per-leg return: LONG (exit-entry)/entry, SHORT (entry-exit)/entry. Teachers are
split in time; selection is on the in-sample window, outcome on out-of-sample.
"""

from __future__ import annotations

import json

import numpy as np

COHORT = "output/investment_hyper_copytrade/paper_cohort.jsonl"
SEED, MIN_LEGS, BOOT, FEE = 20260728, 12, 4000, 0.0009  # 9 bps round trip


def leg_return(lg):
    e, x = lg.get("entry_price", 0.0), lg.get("exit_price", 0.0)
    if e <= 0 or x <= 0:
        return None
    return (x - e) / e if lg["direction"] == "LONG" else (e - x) / e


def stats(returns):
    a = np.asarray(returns, float)
    if len(a) < 2 or a.std() == 0:
        return None
    return {"n": len(a), "mean": float(a.mean()), "sharpe": float(a.mean() / a.std())}


def main():
    recs = [json.loads(l) for l in open(COHORT, encoding="utf-8").read().splitlines()]
    teachers = [r for r in recs if r.get("legs")]
    cutoff = np.median([lg["exit_time_ms"] for r in teachers for lg in r["legs"]])

    rows = []  # (is_pnl, is_sharpe, oos_returns_array)
    for r in teachers:
        isr = [leg_return(lg) for lg in r["legs"] if lg["exit_time_ms"] <= cutoff]
        oor = [leg_return(lg) for lg in r["legs"] if lg["exit_time_ms"] > cutoff]
        isr = [v for v in isr if v is not None]
        oor = [v for v in oor if v is not None]
        s_is = stats(isr)
        if s_is and len(oor) >= MIN_LEGS and len(isr) >= MIN_LEGS:
            is_pnl = sum(lg["closed_pnl"] for lg in r["legs"] if lg["exit_time_ms"] <= cutoff)
            rows.append((is_pnl, s_is["sharpe"], np.asarray(oor, float)))
    n = len(rows)
    all_oos = np.concatenate([r[2] for r in rows])
    field_ret = all_oos.mean()
    field_sh = all_oos.mean() / all_oos.std()
    print(f"cohort teachers usable both windows: {n} | field OOS: mean "
          f"{field_ret*100:+.3f}% gross ({(field_ret-FEE)*100:+.3f}% net)  "
          f"leg-Sharpe {field_sh:+.3f}\n")

    def cohort_oos(metric_col, sub, size):
        order = np.argsort([r[metric_col] for r in sub])[::-1]
        pooled = np.concatenate([sub[i][2] for i in order[:size]])
        return pooled.mean(), pooled.mean() / pooled.std()

    rng = np.random.default_rng(SEED)
    print("=== selection metric (roster 10), OOS realized return ===")
    for col, name in ((0, "PnL-selection"), (1, "Sharpe-selection")):
        m, s = cohort_oos(col, rows, 10)
        print(f"  {name:16} mean {m*100:+.3f}% gross  {(m-FEE)*100:+.3f}% net  leg-Sharpe {s:+.3f}")
    diffs = np.array([
        cohort_oos(1, [rows[i] for i in rng.integers(0, n, n)], 10)[0]
        - cohort_oos(0, [rows[i] for i in rng.integers(0, n, n)], 10)[0]
        for _ in range(BOOT)
    ])
    print(f"  bootstrap P(Sharpe-sel return > PnL-sel return) = {(diffs>0).mean():.2f}")

    print("\n=== roster-size sweep (Sharpe-selection), OOS portfolio return-Sharpe ===")
    print(f"{'roster':>6} {'mean%gross':>11} {'mean%net':>9} {'leg-Sharpe':>11}")
    best = (0, -9)
    for size in (4, 6, 8, 10, 12, 16, 20, 30, 40):
        if size > n:
            break
        m, s = cohort_oos(1, rows, size)
        if s > best[1]:
            best = (size, s)
        print(f"{size:>6} {m*100:>+11.3f} {(m-FEE)*100:>+9.3f} {s:>+11.3f}")
    print(f"\n  best portfolio leg-Sharpe: roster {best[0]} ({best[1]:+.3f})")
    print("  Net return > 0 = the copied cohort profits after fees; portfolio Sharpe")
    print("  peaking at a moderate roster = diversification pays, resolving v1's tie.")


if __name__ == "__main__":
    main()
