"""Self-improvement test: does Sharpe-selection beat PnL-selection out-of-sample?

We changed leader selection from raw PnL to per-leg Sharpe. This asks whether that
is an improvement in OUTCOME, not just in theory: split each registry teacher's
legs in time, select the top-N cohort by an in-sample metric, and measure the
cohort's OUT-OF-SAMPLE per-leg Sharpe (size-invariant -- the registry has no exit
prices, so returns are unavailable; Sharpe is the honest size-neutral quality
proxy for "what a scaled copy inherits"). Bootstrapped over teachers so the
verdict is a confidence interval, not one lucky draw.

Reports, for several roster sizes: OOS cohort Sharpe under PnL-selection vs
Sharpe-selection vs the field, and the bootstrap P(Sharpe-selection > PnL-selection).
"""

from __future__ import annotations

import json

import numpy as np

REG = "output/investment_hyper_copytrade/teacher_registry.jsonl"
SEED, MIN_LEGS, BOOT = 20260728, 12, 4000


def sharpe(pnls):
    a = np.asarray(pnls, float)
    return float(a.mean() / a.std()) if len(a) >= 2 and a.std() > 0 else 0.0


def main():
    recs = [json.loads(l) for l in open(REG, encoding="utf-8").read().splitlines()]
    teachers = [r for r in recs if r.get("legs")]
    cutoff = np.median([lg["exit_time_ms"] for r in teachers for lg in r["legs"]])

    rows = []  # (is_pnl, is_sharpe, oos_sharpe)
    for r in teachers:
        is_p = [lg["closed_pnl"] for lg in r["legs"] if lg["exit_time_ms"] <= cutoff]
        oos = [lg["closed_pnl"] for lg in r["legs"] if lg["exit_time_ms"] > cutoff]
        if len(is_p) >= MIN_LEGS and len(oos) >= MIN_LEGS:
            rows.append((float(np.sum(is_p)), sharpe(is_p), sharpe(oos)))
    A = np.array(rows)  # columns: is_pnl, is_sharpe, oos_sharpe
    n = len(A)
    field = A[:, 2].mean()
    print(f"teachers usable both windows: {n}   field OOS Sharpe: {field:+.4f}\n")

    def cohort_oos(idx_metric_col, sub, size):
        order = np.argsort(sub[:, idx_metric_col])[::-1]
        return sub[order[:size], 2].mean()

    rng = np.random.default_rng(SEED)
    print(f"{'roster':>6} {'PnL-sel OOS':>12} {'Sharpe-sel OOS':>15} {'field':>8} "
          f"{'diff':>8} {'P(Sharpe>PnL)':>14}")
    for size in (8, 12, 20):
        pnl_oos = cohort_oos(0, A, size)
        shp_oos = cohort_oos(1, A, size)
        diffs = np.empty(BOOT)
        for b in range(BOOT):
            sub = A[rng.integers(0, n, n)]
            diffs[b] = cohort_oos(1, sub, size) - cohort_oos(0, sub, size)
        p_better = float((diffs > 0).mean())
        print(f"{size:>6} {pnl_oos:>+12.4f} {shp_oos:>+15.4f} {field:>+8.4f} "
              f"{shp_oos - pnl_oos:>+8.4f} {p_better:>13.2f}{'*' if p_better > 0.95 else ''}")

    print("\nP(Sharpe>PnL) > 0.95 = Sharpe-selection reliably yields a higher-Sharpe")
    print("cohort out-of-sample -> the selection change is a real improvement. Near")
    print("0.5 = the two metrics are interchangeable and the win is elsewhere (breadth).")


if __name__ == "__main__":
    main()
