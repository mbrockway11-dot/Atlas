"""Hunt for a tradeable relationship BETWEEN coin prices (the missing families).

Three analyses on the 1h panel, all judged out-of-sample and cost-adjusted:

1. Correlation structure -- which coins move together, and is it stable
   train->test (a relationship that isn't stable can't be traded).
2. Lead-lag -- does coin A's move predict coin B's next-hour move? Every ordered
   pair tested; a real lead-lag must clear a Bonferroni bar, not just look good.
3. Pairs mean-reversion (relative value) -- fit a hedge ratio on train, z-score
   the spread, and on test trade the spread back to its mean when it stretches.
   The headline is the POOLED result across ALL pairs (no pair-picking), so a
   lucky pair can't fake an edge; per-pair hit distribution is shown alongside.

    .venv/Scripts/python.exe scripts/relationship_hunt.py --cost-bps 10
"""

from __future__ import annotations

import argparse
import math
from itertools import combinations, permutations
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("data/market_prices")


def load_closes() -> pd.DataFrame:
    series = {}
    for p in sorted(REPO.glob("*/1h.csv")):
        df = pd.read_csv(p)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        s = df.dropna(subset=["timestamp", "close"]).set_index("timestamp")["close"]
        s = s[~s.index.duplicated(keep="last")]
        if len(s) > 1000:
            series[p.parent.name] = s
    return pd.DataFrame(series).sort_index().dropna(how="any")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cost-bps", type=float, default=10.0, help="one-way per-leg cost")
    ap.add_argument("--entry-z", type=float, default=2.0)
    ap.add_argument("--exit-z", type=float, default=0.5)
    ap.add_argument("--train-frac", type=float, default=0.70)
    args = ap.parse_args(argv)
    cost_leg = args.cost_bps / 10000.0

    px = load_closes()
    assets = list(px.columns)
    rets = np.log(px).diff().dropna()
    n = len(px)
    cut = int(n * args.train_frac)
    print(f"{len(assets)} coins, {n} aligned 1h bars. train {cut} / test {n-cut}.\n")

    # 1. Correlation structure (stability train vs test).
    ctr = rets.iloc[:cut].corr()
    cte = rets.iloc[cut:].corr()
    pairs = list(combinations(assets, 2))
    corrs = sorted(((a, b, ctr.loc[a, b], cte.loc[a, b]) for a, b in pairs),
                   key=lambda x: x[2], reverse=True)
    print("=== 1. CORRELATION (hourly returns) -- top pairs, train vs test ===")
    for a, b, tr, te in corrs[:6]:
        print(f"  {a:9}/{b:9}  train {tr:+.2f}  test {te:+.2f}")
    print(f"  mean |corr|: train {ctr.abs().values[np.triu_indices(len(assets),1)].mean():.2f}")

    # 2. Lead-lag: does A[t] predict B[t+1]?  (pooled + Bonferroni best)
    print("\n=== 2. LEAD-LAG (A's move -> B's next hour), out-of-sample ===")
    ll = []
    for a, b in permutations(assets, 2):
        ra, rb = rets[a].values, rets[b].values
        x, y = ra[:-1], rb[1:]  # A now, B next
        xtr, ytr, xte, yte = x[:cut], y[:cut], x[cut:], y[cut:]
        if np.std(xtr) == 0:
            continue
        sign = 1.0 if np.corrcoef(xtr, ytr)[0, 1] >= 0 else -1.0
        pos = np.sign(xte) * sign
        net = pos * yte - (np.abs(pos) > 0) * cost_leg
        m = net.mean()
        t = m / (net.std(ddof=1) / math.sqrt(len(net))) if net.std() > 0 else 0.0
        ll.append((a, b, m * 10000, t))
    ll.sort(key=lambda z: z[3], reverse=True)
    from statistics import NormalDist
    bonf = NormalDist().inv_cdf(1 - (0.05 / len(ll)) / 2)
    for a, b, m, t in ll[:4]:
        print(f"  {a:9}->{b:9}  net {m:+.1f}bp/hr  t={t:+.2f}")
    survivors_ll = [z for z in ll if z[3] > bonf and z[2] > 0]
    print(f"  tested {len(ll)} ordered pairs; Bonferroni t-bar ~{bonf:.2f}; survivors: {len(survivors_ll)}")

    # 3. Pairs mean-reversion (relative value).  Pooled across ALL pairs.
    print("\n=== 3. PAIRS SPREAD MEAN-REVERSION (relative value), out-of-sample ===")
    logpx = np.log(px)
    all_trades = []          # pooled net returns across every pair
    pair_summ = []
    roundtrip_cost = 4.0 * cost_leg   # enter+exit, two legs each
    win = 168                # rolling window (1 week) for the reversion level
    max_hold = 336           # force-close after 2 weeks (divergence stop)
    for a, b in pairs:
        la, lb = logpx[a].values, logpx[b].values
        beta = np.polyfit(lb[:cut], la[:cut], 1)[0]
        spread = pd.Series(la - beta * lb)
        rmean = spread.rolling(win).mean()
        rstd = spread.rolling(win).std()
        z = ((spread - rmean) / rstd).values
        sp = spread.values
        pos, entry, held = 0, 0.0, 0
        trades = []
        for t in range(cut, n):
            if not np.isfinite(z[t]):
                continue
            if pos == 0:
                if z[t] > args.entry_z:
                    pos, entry, held = -1, sp[t], 0
                elif z[t] < -args.entry_z:
                    pos, entry, held = 1, sp[t], 0
            else:
                held += 1
                # Close on reversion, on the divergence stop, or at the very end.
                if abs(z[t]) < args.exit_z or held >= max_hold or t == n - 1:
                    trades.append(pos * (sp[t] - entry) - roundtrip_cost)
                    pos = 0
        if len(trades) >= 5:   # need enough closed trades to mean anything
            all_trades.extend(trades)
            arr = np.array(trades)
            pair_summ.append((a, b, len(trades), arr.mean() * 10000, (arr > 0).mean()))

    if all_trades:
        arr = np.array(all_trades)
        m = arr.mean()
        t = m / (arr.std(ddof=1) / math.sqrt(len(arr))) if arr.std() > 0 else 0.0
        pos_pairs = sum(1 for s in pair_summ if s[3] > 0)
        print(f"  POOLED across all {len(pair_summ)} pairs: {len(arr)} trades")
        print(f"    mean net/trade {m*10000:+.1f}bp   win {(arr>0).mean()*100:.1f}%   t={t:+.2f}")
        print(f"    pairs net-positive OOS: {pos_pairs}/{len(pair_summ)} "
              f"(chance would be ~{len(pair_summ)//2})")
        pair_summ.sort(key=lambda s: s[3], reverse=True)
        print("    best pairs (may be luck):")
        for a, b, ntr, mb, wr in pair_summ[:4]:
            print(f"      {a:9}/{b:9}  {ntr:>3} trades  {mb:+.0f}bp/trade  win {wr*100:.0f}%")
        verdict = ("REAL edge (pooled clears cost + t>3 + majority of pairs positive)"
                   if (m > 0 and t > 3 and pos_pairs > 0.65 * len(pair_summ))
                   else "no robust pooled edge")
        print(f"  VERDICT: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
