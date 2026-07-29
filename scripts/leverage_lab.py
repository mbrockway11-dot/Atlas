"""Leverage lab: design high-leverage, high-win-rate bets that actually survive.

Models a perp-style trade as a price race between a take-profit barrier (+tp%
price move) and a stop/liquidation barrier (-sl% price move), with an optional
per-step drift = your directional EDGE. Reports the win rate the geometry forces,
the expected value on collateral net of funding + spread, the Kelly-optimal
leverage, and the probability of ruin from Monte-Carlo simulation.

Key truths it makes concrete:
- win rate is set by sl/(tp+sl) -- a dial, not an edge;
- with zero edge (drift=0) every leverage is negative-EV after costs;
- with an edge there is a best leverage; beyond it, growth falls then ruin.

    .venv/Scripts/python.exe scripts/leverage_lab.py --tp-price-pct 0.7 \
        --sl-price-pct 1.12 --leverage 71 --edge-bps-per-step 0
"""

from __future__ import annotations

import argparse
import math

import numpy as np


def simulate(rng, tp, sl, drift, vol, max_steps):
    """One trade: random-walk price from 0 until it hits +tp or -sl. Returns +1/-1."""
    x = 0.0
    for _ in range(max_steps):
        x += drift + vol * rng.standard_normal()
        if x >= tp:
            return 1
        if x <= -sl:
            return -1
    return 1 if x >= 0 else -1  # timeout: settle by side


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tp-price-pct", type=float, default=0.7, help="take-profit price move %%")
    p.add_argument("--sl-price-pct", type=float, default=1.12, help="stop/liq price move %%")
    p.add_argument("--leverage", type=float, default=71.0)
    p.add_argument("--edge-bps-per-step", type=float, default=0.0, help="directional edge (drift) per step, bps")
    p.add_argument("--vol-bps-per-step", type=float, default=25.0, help="price vol per step, bps")
    p.add_argument("--funding-bps-per-step", type=float, default=1.0, help="funding on notional per step")
    p.add_argument("--spread-bps", type=float, default=5.0, help="one-way spread crossed on entry and exit")
    p.add_argument("--stake-fraction", type=float, default=1.0, help="account fraction risked per trade")
    p.add_argument("--n-trades", type=int, default=200)
    p.add_argument("--sims", type=int, default=4000)
    args = p.parse_args(argv)

    tp, sl = args.tp_price_pct / 100.0, args.sl_price_pct / 100.0
    drift, vol = args.edge_bps_per_step / 10000.0, args.vol_bps_per_step / 10000.0
    funding = args.funding_bps_per_step / 10000.0
    spread = 2.0 * args.spread_bps / 10000.0  # entry + exit
    lev = args.leverage
    rng = np.random.default_rng(0)
    max_steps = 5000

    # Sample trades once to estimate win rate + mean hold, reuse for all sims.
    N = 20000
    outcomes = np.empty(N)
    holds = np.empty(N)
    for i in range(N):
        x = 0.0
        s = 0
        while s < max_steps:
            x += drift + vol * rng.standard_normal()
            s += 1
            if x >= tp or x <= -sl:
                break
        outcomes[i] = 1 if x >= tp else -1
        holds[i] = s
    win_rate = float((outcomes > 0).mean())
    mean_hold = float(holds.mean())

    # Collateral return per trade (win: +lev*tp, loss: -min(lev*sl,1)), net of costs.
    win_ret = lev * tp
    loss_ret = -min(lev * sl, 1.0)  # capped at liquidation
    cost = funding * lev * mean_hold + spread * lev
    ev = win_rate * win_ret + (1 - win_rate) * loss_ret - cost

    # Kelly-optimal leverage for THIS edge (search leverage that maximizes E[log]).
    def growth_at(L):
        wr_L = win_rate
        wret = L * tp
        lret = -min(L * sl, 1.0)
        c = funding * L * mean_hold + spread * L
        f = args.stake_fraction
        g_win = math.log(max(1e-9, 1 + f * (wret - c)))
        g_loss = math.log(max(1e-9, 1 + f * (lret - c)))
        return wr_L * g_win + (1 - wr_L) * g_loss

    grid = np.linspace(0.0, max(80.0, lev * 1.2), 400)
    growths = [growth_at(L) for L in grid]
    best_L = float(grid[int(np.argmax(growths))])

    # Monte-Carlo the account over n_trades at the chosen leverage.
    finals = np.empty(args.sims)
    ruined = 0
    for s in range(args.sims):
        eq = 1.0
        wins = rng.random(args.n_trades) < win_rate
        for w in wins:
            r = (win_ret if w else loss_ret) - cost
            eq *= 1 + args.stake_fraction * r
            if eq < 0.01:
                ruined += 1
                eq = 0.0
                break
        finals[s] = eq

    print(f"Setup: {tp*100:.2f}% take-profit vs {sl*100:.2f}% stop, {lev:.0f}x leverage, "
          f"edge {args.edge_bps_per_step:.1f}bps/step")
    print(f"  win rate (forced by geometry): {win_rate*100:.1f}%   avg hold {mean_hold:.0f} steps")
    print(f"  per-win {win_ret*100:+.0f}%  per-loss {loss_ret*100:+.0f}%  cost/trade {cost*100:.1f}%")
    print(f"  EXPECTED VALUE per trade: {ev*100:+.2f}% of collateral")
    print(f"  break-even win rate needed: {(-loss_ret+cost)/(win_ret-loss_ret)*100:.1f}%")
    print(f"  KELLY-OPTIMAL leverage for this edge: {best_L:.1f}x  (you used {lev:.0f}x)")
    print(f"  over {args.n_trades} trades x {args.sims} sims at {lev:.0f}x, stake {args.stake_fraction:.0%}:")
    print(f"    median final account: {np.median(finals):.3f}x   "
          f"profitable sims: {(finals>1).mean()*100:.0f}%   "
          f"ruin (<1% left): {ruined/args.sims*100:.0f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
