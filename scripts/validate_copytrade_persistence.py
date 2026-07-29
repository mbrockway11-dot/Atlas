"""Does copy-trading top Hyperliquid teachers actually work? (forward validation)

The core premise of the whole product: a trader who performed well keeps
performing well, so copying the top ones profits going forward. If past
performance does NOT predict future performance, copy-trading top-PnL traders is
chasing noise -- and raw-PnL selection makes it worse.

Test, on the 288 registry teachers (152k reconstructed legs, each with closed_pnl
and timestamps): split every teacher's legs at a global time cutoff into an
in-sample (IS) and out-of-sample (OOS) window. Then:

  1. PERSISTENCE -- does an IS metric predict the same teacher's OOS metric?
     (Spearman across teachers.) Compared for raw total PnL (the current metric,
     size-confounded) vs per-leg Sharpe (mean/std of leg PnL -- scale-invariant,
     the skill signal).
  2. THE EDGE -- if we SELECT the top quartile by an IS metric, is their OOS
     performance actually positive, and better than the bottom quartile / all?
     Permutation null. This is the direct "would copying them have paid" test.
"""

from __future__ import annotations

import json

import numpy as np

REG = "output/investment_hyper_copytrade/teacher_registry.jsonl"
SEED, MIN_LEGS = 20260728, 12


def metrics(legs):
    pnl = np.array([lg["closed_pnl"] for lg in legs], float)
    if len(pnl) < 2 or pnl.std() == 0:
        return None
    return {
        "n": len(pnl),
        "total_pnl": float(pnl.sum()),
        "sharpe": float(pnl.mean() / pnl.std()),   # scale-invariant per-leg skill
        "win_rate": float((pnl > 0).mean()),
    }


def spearman(a, b):
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def main():
    recs = [json.loads(l) for l in open(REG, encoding="utf-8").read().splitlines()]
    teachers = [r for r in recs if r.get("legs")]
    all_exit = np.array([lg["exit_time_ms"] for r in teachers for lg in r["legs"]], float)
    cutoff = np.median(all_exit)
    from datetime import datetime, timezone
    print(f"teachers with legs: {len(teachers)} | cutoff "
          f"{datetime.fromtimestamp(cutoff/1000, timezone.utc):%Y-%m-%d} "
          f"(IS before, OOS after)\n")

    rows = []
    for r in teachers:
        is_legs = [lg for lg in r["legs"] if lg["exit_time_ms"] <= cutoff]
        oos_legs = [lg for lg in r["legs"] if lg["exit_time_ms"] > cutoff]
        if len(is_legs) < MIN_LEGS or len(oos_legs) < MIN_LEGS:
            continue
        mi, mo = metrics(is_legs), metrics(oos_legs)
        if mi and mo:
            rows.append((r["address"], mi, mo))
    print(f"teachers with >= {MIN_LEGS} legs in BOTH windows: {len(rows)}\n")

    print("=== 1. PERSISTENCE (Spearman: does IS metric predict OOS metric?) ===")
    for key in ("total_pnl", "sharpe", "win_rate"):
        a = np.array([r[1][key] for r in rows])
        b = np.array([r[2][key] for r in rows])
        rho = spearman(a, b)
        label = {"total_pnl": "raw total PnL (current metric)", "sharpe": "per-leg Sharpe (risk-adj)",
                 "win_rate": "win rate"}[key]
        print(f"  {label:32} rho = {rho:+.3f}  {'persists' if rho > 0.15 else 'NO persistence'}")

    print("\n=== 2. THE EDGE: select top quartile by IS metric -> OOS outcome ===")
    rng = np.random.default_rng(SEED)
    n = len(rows)
    for sel_key in ("total_pnl", "sharpe"):
        sel = np.array([r[1][sel_key] for r in rows])
        oos_sharpe = np.array([r[2]["sharpe"] for r in rows])
        oos_pnl = np.array([r[2]["total_pnl"] for r in rows])
        order = np.argsort(sel)[::-1]
        top = order[:n // 4]; bot = order[-(n // 4):]
        top_oos, bot_oos = oos_sharpe[top].mean(), oos_sharpe[bot].mean()
        # permutation null: random quartile's OOS sharpe
        null = np.array([oos_sharpe[rng.choice(n, n // 4, replace=False)].mean() for _ in range(5000)])
        p = float((null >= top_oos).mean())
        print(f"  select by {sel_key:10}: top-quartile OOS Sharpe {top_oos:+.4f} "
              f"(bottom {bot_oos:+.4f}, all {oos_sharpe.mean():+.4f})  p={p:.4f}  "
              f"{'<-- edge' if p < 0.05 else 'no edge'}")
        print(f"                     top-quartile OOS total PnL: ${oos_pnl[top].sum():,.0f} "
              f"(bottom ${oos_pnl[bot].sum():,.0f})")

    print("\nPersistence rho>0 and top-quartile OOS Sharpe>0 beyond null = a real edge;")
    print("if sharpe persists but raw PnL does not, the selection metric must change.")


if __name__ == "__main__":
    main()
