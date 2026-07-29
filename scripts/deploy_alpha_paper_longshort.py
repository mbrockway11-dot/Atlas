"""Deploy the validated alpha config to paper with a SHORT-CAPABLE path.

Read-only market data; paper-only execution. Unlike the long-only
`deploy_alpha_paper.py` (which the long-only portfolio bridge forced), this
builds SIGNED target exposures from the two promoted engines -- LONG on net-long
assets, SHORT on net-short assets -- and executes each leg through
`run_paper_execution` with `RiskLimits(allow_short_positions=True)`, threading
the account across intents. So the defensive engine's hedge leg actually trades.

Two modes:
  live (default): current signals + live snapshot prices. In a risk-on market the
    defensive engine is flat, so the book may be all-long -- that is correct, not
    a bug.
  --features-date YYYY-MM-DD: run the engines on that historical feature row
    (from market_feature_history.csv) and execute at that day's close. Use a
    risk-off date to demonstrate the short leg filling end to end.

    .venv/Scripts/python.exe scripts/deploy_alpha_paper_longshort.py
    .venv/Scripts/python.exe scripts/deploy_alpha_paper_longshort.py --features-date 2025-03-01
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from atlas.investment.alpha.engines.defensive_risk_off import DefensiveRiskOffEngine
from atlas.investment.alpha.engines.drawdown_recovery import DrawdownRecoveryEngine
from atlas.investment.execution.account_store import (
    AccountSnapshot,
    account_from_mapping,
)
from atlas.investment.execution.contracts import OrderIntent, RiskLimits
from atlas.investment.execution.service import run_paper_execution

PROMOTED_ENGINES = (DrawdownRecoveryEngine(), DefensiveRiskOffEngine())
LATEST = Path("output/investment_alpha_engines/alpha_engine_latest.csv")
HISTORY = Path("output/investment_alpha/market_feature_history.csv")
SNAPSHOT = Path("output/investment_market_data/latest_market_snapshot.json")


def signed_targets(signals: pd.DataFrame, *, gross: float) -> dict[str, float]:
    """Net signed target weight per asset from LONG/SHORT conviction."""
    sign = signals["direction"].map(
        {"LONG": 1.0, "SHORT": -1.0}
    ).fillna(0.0)
    signals = signals.assign(_signed=signals["conviction"] * sign)
    net = signals.groupby("asset")["_signed"].sum()
    net = net[net.abs() > 1e-6]
    denom = net.abs().sum()
    if denom <= 0:
        return {}
    return (net / denom * gross).to_dict()


def snapshot_prices(path: Path) -> dict[str, float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    prices: dict[str, float] = {}
    refs = payload.get("reference_prices")
    if isinstance(refs, dict):
        for sym, px in refs.items():
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


def live_inputs() -> tuple[pd.DataFrame, dict[str, float]]:
    signals = pd.read_csv(LATEST)
    ids = {e.metadata.engine_id for e in PROMOTED_ENGINES}
    return signals[signals["engine_id"].isin(ids)], snapshot_prices(SNAPSHOT)


def historical_inputs(date: str) -> tuple[pd.DataFrame, dict[str, float]]:
    hist = pd.read_csv(HISTORY)
    hist["_d"] = hist["timestamp"].astype(str).str[:10]
    frame = hist[hist["_d"] == date].copy()
    if frame.empty:
        raise SystemExit(f"No feature rows for {date}")
    sig = pd.concat([e.run(frame) for e in PROMOTED_ENGINES], ignore_index=True)
    prices = {
        str(r["asset"]).upper(): float(r["close"])
        for _, r in frame.iterrows()
        if float(r.get("close", 0) or 0) > 0
    }
    return sig, prices


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features-date", default=None)
    parser.add_argument("--initial-cash", type=float, default=10_000.0)
    parser.add_argument("--gross-fraction", type=float, default=0.90)
    parser.add_argument("--max-leverage", type=float, default=1.5)
    args = parser.parse_args(argv)

    if args.features_date:
        signals, prices = historical_inputs(args.features_date)
        print(f"Mode: historical features {args.features_date}")
    else:
        signals, prices = live_inputs()
        print("Mode: live signals + snapshot prices")

    targets = signed_targets(signals, gross=args.gross_fraction)
    targets = {a: w for a, w in targets.items() if a in prices}
    if not targets:
        print("No priced targets to execute.", file=sys.stderr)
        return 1

    longs = {a: w for a, w in targets.items() if w > 0}
    shorts = {a: w for a, w in targets.items() if w < 0}
    print(f"\nSigned target book ({len(longs)} long, {len(shorts)} short):")
    for a, w in sorted(targets.items(), key=lambda kv: kv[1]):
        side = "SHORT" if w < 0 else "LONG "
        print(f"  {side} {a:10} weight {w:+.3f}  @ ${prices[a]:,.4f}")

    limits = RiskLimits(
        allow_short_positions=True,
        maximum_leverage=args.max_leverage,
        maximum_order_notional=5_000.0,
        maximum_asset_notional=10_000.0,
    )
    account = AccountSnapshot(cash=float(args.initial_cash))

    # Execute shorts first (free margin), then longs, threading the account.
    ordered = sorted(targets.items(), key=lambda kv: kv[1])
    fills_total = 0
    for i, (asset, weight) in enumerate(ordered):
        price = prices[asset]
        quantity = abs(weight) * args.initial_cash / price
        side = "SELL" if weight < 0 else "BUY"
        intent = OrderIntent(
            asset=asset,
            side=side,
            quantity=round(quantity, 8),
            reference_price=price,
            strategy_id="promoted_alpha_longshort",
            evidence_id=f"dr+defensive:{asset}",
        )
        report = run_paper_execution(
            intent=intent,
            account=account,
            limits=limits,
            write_outputs=(i == len(ordered) - 1),
        )
        if not report["risk"]["approved"]:
            print(f"  [risk-rejected] {side} {asset}: {report['risk'].get('reason_codes')}")
            continue
        fills_total += len(report.get("fills", []))
        account = account_from_mapping(report["account_after"])

    print(
        f"\nExecuted: {fills_total} paper fill(s)  |  "
        f"paper_only={report['contract']['paper_only']}  "
        f"live_execution={report['live_execution']}  "
        f"credentials_used={report['contract']['live_credentials_used']}"
    )
    positions = report["account_after"].get("positions", [])
    print(f"\nResulting paper book (cash ${report['account_after'].get('cash', 0):,.2f}):")
    for p in positions if isinstance(positions, list) else positions.values():
        qty = float(p.get("quantity", 0))
        if abs(qty) < 1e-9:
            continue
        book = "SHORT" if qty < 0 else "LONG "
        print(f"  {book} {p.get('asset'):10} qty {qty:+.4f} @ ${float(p.get('average_price',0)):,.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
