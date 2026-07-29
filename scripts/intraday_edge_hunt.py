"""Hunt for a leverageable intraday edge in the 1h charts -- rigorously.

Scans a panel of candidate hourly signals (momentum, mean-reversion, RSI,
breakout, range-position, volatility regime, SMA distance) against forward
returns, and judges each ONLY on out-of-sample, cost-adjusted performance:

- entries are sampled non-overlapping (every H hours), so overlapping-bar
  Sharpe inflation is avoided;
- the signal's direction is fit on the first 70% of time (train) and the edge
  is measured on the last 30% (test) it never saw;
- every test trade pays a round-trip cost;
- results pool across all 10 assets.

Many candidates are tested, so some will look good by chance -- the report
prints how many were scanned and treats a lone survivor with suspicion, not
celebration. A real edge shows a consistent train->test sign AND a test result
that clears cost with a t-stat that survives the multiple-testing discount.

    .venv/Scripts/python.exe scripts/intraday_edge_hunt.py --cost-bps 10
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("data/market_prices")


def load_1h() -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for p in sorted(REPO.glob("*/1h.csv")):
        df = pd.read_csv(p)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        for c in ("open", "high", "low", "close", "volume"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna(subset=["timestamp", "close"]).sort_values("timestamp")
        if len(df) > 500:
            out[p.parent.name] = df.reset_index(drop=True)
    return out


def signals(df: pd.DataFrame) -> pd.DataFrame:
    c = df["close"]
    ret1 = c.pct_change()
    f = pd.DataFrame(index=df.index)
    # Momentum / trend (positive = expect continuation up)
    f["mom_4h"] = c.pct_change(4)
    f["mom_12h"] = c.pct_change(12)
    f["mom_24h"] = c.pct_change(24)
    # Mean reversion (positive value = recently down = expect bounce)
    f["rev_1h"] = -ret1
    f["rev_4h"] = -c.pct_change(4)
    # RSI(6) oversold(+)/overbought(-)
    up = ret1.clip(lower=0).rolling(6).mean()
    dn = (-ret1.clip(upper=0)).rolling(6).mean()
    rsi = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    f["rsi_revert"] = (50 - rsi) / 50.0
    # Range position over 24h (high = near top = momentum)
    hi = c.rolling(24).max()
    lo = c.rolling(24).min()
    f["range_pos_24h"] = (c - lo) / (hi - lo)
    # Breakout of prior 24h high/low
    f["breakout_24h"] = np.where(c > hi.shift(1), 1.0, np.where(c < lo.shift(1), -1.0, 0.0))
    # Distance from 24h SMA (trend)
    sma = c.rolling(24).mean()
    f["dist_sma_24h"] = (c - sma) / sma
    # Volatility expansion (short vs long realized vol)
    f["vol_expansion"] = ret1.rolling(6).std() / ret1.rolling(48).std()
    return f


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cost-bps", type=float, default=10.0, help="round-trip cost per trade")
    p.add_argument("--holdings", default="4,12,24", help="holding periods in hours")
    p.add_argument("--train-frac", type=float, default=0.70)
    args = p.parse_args(argv)
    cost = args.cost_bps / 10000.0
    holds = [int(h) for h in args.holdings.split(",")]

    data = load_1h()
    sig_names = list(signals(next(iter(data.values()))).columns)
    print(f"Scanning {len(sig_names)} signals x {len(holds)} holds on {len(data)} assets, "
          f"1h bars, cost {args.cost_bps:.0f}bps round-trip.\n")

    results = []
    for sig in sig_names:
        for H in holds:
            test_rets = []  # pooled OOS net returns across assets
            train_signs = []
            for asset, df in data.items():
                c = df["close"].values
                f = signals(df)[sig].values
                fwd = np.full(len(c), np.nan)
                fwd[:-H] = c[H:] / c[:-H] - 1.0
                idx = np.arange(0, len(c) - H, H)  # non-overlapping entries
                s = f[idx]
                r = fwd[idx]
                ok = np.isfinite(s) & np.isfinite(r)
                s, r = s[ok], r[ok]
                if len(s) < 60:
                    continue
                cut = int(len(s) * args.train_frac)
                s_tr, r_tr, s_te, r_te = s[:cut], r[:cut], s[cut:], r[cut:]
                if len(s_te) < 20 or np.std(s_tr) == 0:
                    continue
                # Fit direction on train: does high signal -> high forward return?
                sign = 1.0 if np.corrcoef(s_tr, r_tr)[0, 1] >= 0 else -1.0
                train_signs.append(sign)
                # Trade on test: long/short by signal side vs its train median.
                med = np.median(s_tr)
                pos = np.sign(s_te - med) * sign
                net = pos * r_te - (np.abs(pos) > 0) * cost
                test_rets.extend(net[np.abs(pos) > 0].tolist())
            if len(test_rets) < 100:
                continue
            arr = np.array(test_rets)
            mean = arr.mean()
            t = mean / (arr.std(ddof=1) / math.sqrt(len(arr))) if arr.std() > 0 else 0.0
            results.append({
                "signal": sig, "hold_h": H, "n_test": len(arr),
                "mean_net_bps": mean * 10000, "hit": (arr > 0).mean(),
                "t_stat": t,
            })

    results.sort(key=lambda x: x["t_stat"], reverse=True)
    n_tested = len(results)
    print(f"{'signal':16} {'hold':>4} {'n':>6} {'mean_net':>10} {'hit%':>6} {'t':>7}")
    print("-" * 58)
    for r in results:
        flag = "  <== survives" if (r["mean_net_bps"] > 0 and r["t_stat"] > 3.0) else ""
        print(f"{r['signal']:16} {r['hold_h']:>3}h {r['n_test']:>6} "
              f"{r['mean_net_bps']:>+8.1f}bp {r['hit']*100:>5.1f}% {r['t_stat']:>+6.2f}{flag}")

    survivors = [r for r in results if r["mean_net_bps"] > 0 and r["t_stat"] > 3.0]
    print(f"\nTested {n_tested} candidates. Bonferroni t-threshold for p<0.05: "
          f"~{ -0 + round(_bonf_t(n_tested),2)}")
    print(f"Survivors (positive net + t>3.0): {len(survivors)}")
    if not survivors:
        print("=> No intraday edge cleared cost + out-of-sample. Honest null result.")
    else:
        for s in survivors:
            print(f"   {s['signal']} @ {s['hold_h']}h: {s['mean_net_bps']:+.1f}bp/trade, t={s['t_stat']:.2f}")
        print("   Treat with suspicion until confirmed on a fresh holdout + real fills.")
    return 0


def _bonf_t(m: int) -> float:
    # Rough two-sided Bonferroni t threshold for p<0.05 over m tests (normal approx).
    from statistics import NormalDist
    alpha = 0.05 / max(1, m)
    return NormalDist().inv_cdf(1 - alpha / 2)


if __name__ == "__main__":
    raise SystemExit(main())
