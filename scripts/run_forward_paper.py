"""Forward paper run of the validated dr + defensive config.

Read-only market data; paper-only, short-capable execution. Each cycle: refresh
live signals from the two promoted engines, accrue perp funding on held
positions since the last cycle, rebalance the paper book to the new signed
target, mark to market at live prices, and append one row to a forward equity
log. The account persists across cycles, so running this on a daily schedule
builds a genuine out-of-sample-in-time track record -- the one test the
backtests could not do.

    .venv/Scripts/python.exe scripts/run_forward_paper.py
    # then schedule daily, e.g. Windows Task Scheduler / cron
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from atlas.investment.alpha.engines.defensive_risk_off import DefensiveRiskOffEngine
from atlas.investment.alpha.engines.drawdown_recovery import DrawdownRecoveryEngine
from atlas.investment.execution.account_store import (
    AccountSnapshot,
    account_from_mapping,
    write_paper_account,
)
from atlas.investment.execution.contracts import OrderIntent, RiskLimits
from atlas.investment.execution.service import run_paper_execution

ENGINES = (DrawdownRecoveryEngine(), DefensiveRiskOffEngine())
LATEST = Path("output/investment_alpha_engines/alpha_engine_latest.csv")
SNAPSHOT = Path("output/investment_market_data/latest_market_snapshot.json")
STATE_DIR = Path("output/investment_forward_paper")
ACCOUNT_JSON = STATE_DIR / "forward_account.json"
STATE_JSON = STATE_DIR / "forward_state.json"
EQUITY_LOG = STATE_DIR / "forward_equity_log.csv"
WEIGHTS_JSON = STATE_DIR / "engine_weights.json"


def engine_weights() -> dict[str, float]:
    """Per-engine weights (self-refinement writes these; default equal)."""
    default = {e.metadata.engine_id: 1.0 for e in ENGINES}
    if WEIGHTS_JSON.exists():
        try:
            loaded = json.loads(WEIGHTS_JSON.read_text("utf-8"))
            return {k: float(loaded.get(k, 1.0)) for k in default}
        except (ValueError, json.JSONDecodeError):
            return default
    return default


def snapshot_prices(path: Path) -> dict[str, float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    prices: dict[str, float] = {}
    for sym, px in (payload.get("reference_prices") or {}).items():
        try:
            prices[str(sym).upper()] = float(px)
        except (TypeError, ValueError):
            continue
    for q in payload.get("quotes", []) or []:
        sym = str(q.get("symbol", "")).upper()
        px = q.get("midpoint") or q.get("last")
        if sym and px and sym not in prices:
            prices[sym] = float(px)
    return prices


def target_notionals(prices: dict[str, float], *, capital: float, gross: float) -> dict[str, float]:
    """Signed target notional per asset from the two engines' live signals."""
    signals = pd.read_csv(LATEST)
    ids = {e.metadata.engine_id for e in ENGINES}
    signals = signals[signals["engine_id"].isin(ids)]
    weights = engine_weights()
    sign = signals["direction"].map({"LONG": 1.0, "SHORT": -1.0}).fillna(0.0)
    ew = signals["engine_id"].map(weights).fillna(1.0)
    net = (signals.assign(s=signals["conviction"] * sign * ew)
           .groupby("asset")["s"].sum())
    net = net[net.abs() > 1e-6]
    net = net[net.index.str.upper().isin(prices)]
    denom = net.abs().sum()
    if denom <= 0:
        return {}
    return {a: float(w / denom * gross * capital) for a, w in net.items()}


def positions_map(account: AccountSnapshot) -> dict[str, float]:
    out: dict[str, float] = {}
    pos = getattr(account, "positions", {}) or {}
    values = pos.values() if isinstance(pos, dict) else pos
    for p in values:
        if isinstance(p, dict):
            out[str(p.get("asset")).upper()] = float(p.get("quantity", 0.0))
        else:
            out[str(p.asset).upper()] = float(p.quantity)
    return out


def net_liquidation(account: AccountSnapshot, prices: dict[str, float]) -> float:
    equity = float(getattr(account, "cash", 0.0))
    for asset, qty in positions_map(account).items():
        equity += qty * prices.get(asset, 0.0)
    return equity


def refuse_live() -> int:
    """The --live path. It does not, and will not, place a live order.

    Live execution requires the operator to enter their own credentials in their
    own environment and place the first order themselves. This tool never handles
    keys, never sends an order, and never decides capital is safe to risk. It
    reports forward-paper readiness against docs/GO_LIVE_CRITERIA.md and stops.
    """
    print("=" * 70)
    print("LIVE EXECUTION IS DISABLED BY DESIGN. No order will be placed.")
    print("=" * 70)
    days = 0
    equities: list[float] = []
    if EQUITY_LOG.exists():
        import csv
        rows = list(csv.DictReader(open(EQUITY_LOG, encoding="utf-8")))
        dates = {r["timestamp"][:10] for r in rows}
        days = len(dates)
        equities = [float(r["equity"]) for r in rows]
    peak, max_dd = (equities[0] if equities else 0.0), 0.0
    for e in equities:
        peak = max(peak, e)
        max_dd = min(max_dd, e / peak - 1.0) if peak else 0.0
    print(f"\nForward-paper readiness (see docs/GO_LIVE_CRITERIA.md):")
    print(f"  forward track:  {days} day(s)   [gate 1 needs >= 90]")
    print(f"  max drawdown:   {max_dd * 100:.1f}%   [gate 3 needs <= 30%]")
    ready = days >= 90 and max_dd >= -0.30
    print(f"\n  readiness (hard gates 1 & 3 shown): {'partial' if not ready else 'preliminary-pass'}")
    print(
        "\nTo go live you must, yourself: (1) review the full checklist in "
        "docs/GO_LIVE_CRITERIA.md against the forward evidence, (2) set up your "
        "own venue credentials in your own environment, (3) place a small, "
        "risk-capped first order by hand. This assistant will not do any of "
        "those steps."
    )
    return 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--initial-cash", type=float, default=10_000.0)
    parser.add_argument("--gross-fraction", type=float, default=0.90)
    parser.add_argument("--max-leverage", type=float, default=1.5)
    parser.add_argument("--funding-bps-per-day", type=float, default=3.0)
    parser.add_argument("--min-rebalance-notional", type=float, default=50.0)
    parser.add_argument(
        "--mark-only",
        action="store_true",
        help="Revalue the held book at live prices and log equity; do NOT rebalance.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="INERT by design: refuses to execute; prints the go-live checklist.",
    )
    args = parser.parse_args(argv)

    if args.live:
        return refuse_live()

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    prices = snapshot_prices(SNAPSHOT)
    if not prices:
        print("No live prices in snapshot.", file=sys.stderr)
        return 1

    # Resume account + state.
    if ACCOUNT_JSON.exists():
        account = account_from_mapping(json.loads(ACCOUNT_JSON.read_text("utf-8")))
    else:
        account = AccountSnapshot(cash=float(args.initial_cash))
    state = json.loads(STATE_JSON.read_text("utf-8")) if STATE_JSON.exists() else {}
    last_run = state.get("last_run")

    starting_equity = net_liquidation(account, prices)

    # Accrue perp funding on held positions since the last cycle.
    funding_paid = 0.0
    if last_run:
        elapsed_days = max(0.0, (now - datetime.fromisoformat(last_run)).total_seconds() / 86400.0)
        gross_notional = sum(abs(q) * prices.get(a, 0.0) for a, q in positions_map(account).items())
        funding_paid = args.funding_bps_per_day / 10000.0 * elapsed_days * gross_notional
        account = AccountSnapshot(
            cash=float(getattr(account, "cash", 0.0)) - funding_paid,
            positions=getattr(account, "positions", {}) or {},
        )

    # Rebalance to the signal target -- unless this is a mark-only tick, which
    # just revalues the existing book at live prices (signals only change daily,
    # so re-trading intraday only churns fees).
    fills = 0
    if not args.mark_only:
        targets = target_notionals(prices, capital=starting_equity or args.initial_cash,
                                   gross=args.gross_fraction)
        current = positions_map(account)
        limits = RiskLimits(allow_short_positions=True, maximum_leverage=args.max_leverage,
                            maximum_order_notional=5_000.0, maximum_asset_notional=10_000.0)
        assets = sorted(set(targets) | set(current), key=lambda a: targets.get(a, 0.0))
        for asset in assets:
            price = prices.get(asset)
            if not price:
                continue
            target_qty = targets.get(asset, 0.0) / price
            diff_qty = target_qty - current.get(asset, 0.0)
            if abs(diff_qty) * price < args.min_rebalance_notional:
                continue
            report = run_paper_execution(
                intent=OrderIntent(
                    asset=asset, side="BUY" if diff_qty > 0 else "SELL",
                    quantity=round(abs(diff_qty), 8), reference_price=price,
                    strategy_id="forward_dr_defensive", evidence_id=f"forward:{asset}",
                ),
                account=account, limits=limits, write_outputs=False,
            )
            if report["risk"]["approved"]:
                fills += len(report.get("fills", []))
                account = account_from_mapping(report["account_after"])

    ending_equity = net_liquidation(account, prices)

    # Persist + log.
    ACCOUNT_JSON.write_text(json.dumps(account.to_dict(), sort_keys=True, indent=2) + "\n", "utf-8")
    STATE_JSON.write_text(json.dumps({"last_run": now.isoformat()}, indent=2) + "\n", "utf-8")
    pos = positions_map(account)
    longs = {a: q for a, q in pos.items() if q > 1e-9}
    shorts = {a: q for a, q in pos.items() if q < -1e-9}
    gross = sum(abs(q) * prices.get(a, 0.0) for a, q in pos.items())
    row = {
        "timestamp": now.isoformat(), "equity": round(ending_equity, 2),
        "cash": round(float(getattr(account, "cash", 0.0)), 2),
        "funding_paid": round(funding_paid, 4), "fills": fills,
        "n_long": len(longs), "n_short": len(shorts),
        "gross_exposure": round(gross, 2),
    }
    header = not EQUITY_LOG.exists()
    with EQUITY_LOG.open("a", encoding="utf-8", newline="") as fh:
        import csv
        w = csv.DictWriter(fh, fieldnames=list(row))
        if header:
            w.writeheader()
        w.writerow(row)

    print("Forward paper cycle:")
    print(f"  time {now.isoformat()}  (prev run: {last_run or 'first cycle'})")
    print(f"  funding accrued: ${funding_paid:,.2f}  |  rebalance fills: {fills}")
    print(f"  equity: ${starting_equity:,.2f} -> ${ending_equity:,.2f}")
    print(f"  book: {len(longs)} long / {len(shorts)} short  gross ${gross:,.0f}  cash ${row['cash']:,.0f}")
    print(f"  logged -> {EQUITY_LOG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
