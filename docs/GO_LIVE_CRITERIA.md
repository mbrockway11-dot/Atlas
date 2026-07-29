# Go-Live Readiness Criteria (pre-registered 2026-07-26)

These thresholds are fixed **before** the forward paper run accumulates, so the
bar cannot be moved later to fit a result. The config in question is the
`drawdown_recovery_v1` + `defensive_risk_off_v1` ensemble.

**Nothing in this repo goes live automatically. Ever.** The `--live` switch is
inert by design (see `run_forward_paper.py`): it refuses to execute and prints
this checklist. Arming live trading requires a human to enter their own
credentials in their own environment and place the first order themselves. The
assistant does not execute trades, handle keys, or decide that capital is safe
to risk — those are the operator's decisions.

## Hard gates — ALL must hold, on FORWARD paper data (not backtest)

| # | Criterion | Threshold | Why |
|---|---|---|---|
| 1 | Forward paper track length | ≥ **90 trading days** live-forward | A few weeks is noise; a quarter spans conditions |
| 2 | Forward Sharpe vs backtest | forward ≥ **0.6 ×** backtest (~0.74+) | Backtests overstate; large decay = the edge wasn't real |
| 3 | Forward max drawdown | ≤ **30%** | Above this the sizing is wrong for the operator's risk |
| 4 | Cost-adjusted return | positive **after** modeled funding + slippage | On real perps, funding/slippage can erase the edge |
| 5 | Single-asset loss contribution | no one asset > **40%** of total loss | Concentration blowup check |
| 6 | Regime coverage | forward window includes ≥ **1 drawdown ≥ 15%** in the market | Must see it behave when the market falls, not just rise |
| 7 | Self-refinement stability | learned engine weights stayed within bounds, no circuit-breaker trips | A tuner that thrashed is chasing noise |

## Soft checks — reviewed, not auto-blocking

- Forward win rate and profit factor broadly consistent with backtest.
- Defensive short leg actually activated in a risk-off stretch (not just theory).
- Turnover and fee drag within the modeled assumptions.

## What "enough data to feel safe" honestly requires

Even with all gates green, this is a **backtest-plus-one-quarter** on a
designer-biased engine over correlated crypto with a simplified cost model. That
is the *minimum* to consider a small, risk-capped live pilot — not a mandate.
The known residuals (designer bias, no real funding/borrow in the paper model,
single asset class, short history) do not disappear because a checklist passes.

## The one-way door

Going live risks real money and is irreversible per trade. It is a decision only
the operator can make, after reviewing the forward evidence against this list,
with position sizes they can afford to lose. The tooling makes that flip a
single deliberate human action — never an automatic one.
