
"""Portfolio State v3 builder."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

import pandas as pd


INITIAL_EQUITY = 100000.0


def build_portfolio_state(inputs: dict[str, Any]) -> dict[str, Any]:
    mtm_report = inputs.get("mtm_report", {}) or {}
    mtm_positions = inputs.get("mtm_positions")
    fills = inputs.get("paper_broker_fills")
    ledger = inputs.get("paper_broker_ledger")
    broker_orders = inputs.get("broker_orders")
    decision = inputs.get("decision", {}) or {}

    if mtm_positions is not None and not mtm_positions.empty:
        pf = portfolio_from_mtm(mtm_positions, mtm_report)
        state_source = "mark_to_market_v2"
    elif fills is not None and not fills.empty:
        pf = portfolio_from_broker_fills(fills, broker_orders)
        state_source = "paper_broker_v2"
    else:
        return empty_state()

    pf["paper_weight"] = pd.to_numeric(pf.get("paper_weight", 0.0), errors="coerce").fillna(0.0)
    pf["paper_value"] = pd.to_numeric(pf.get("paper_value", 0.0), errors="coerce").fillna(0.0)

    risky = pf[~pf["asset"].isin(["CASH", "RESERVED_CASH"])]
    cash = pf[pf["asset"] == "CASH"]
    reserved = pf[pf["asset"] == "RESERVED_CASH"]

    equity_snapshot = mtm_report.get("equity_snapshot", {}) or {}
    current_equity = float(equity_snapshot.get("equity") or pf["paper_value"].sum())
    pnl_value = float(equity_snapshot.get("pnl") or (current_equity - INITIAL_EQUITY))
    pnl_pct = float(equity_snapshot.get("pnl_pct") or (pnl_value / INITIAL_EQUITY if INITIAL_EQUITY else 0.0))
    drawdown = float(equity_snapshot.get("drawdown") or 0.0)

    risk_decision = decision.get("risk_adjusted_decision", {}) or {}
    ledger_rows = ledger.to_dict("records") if ledger is not None and not ledger.empty else []
    pending_orders = broker_orders.to_dict("records") if broker_orders is not None and not broker_orders.empty else []

    return {
        "success": True,
        "timestamp": datetime.now(UTC).isoformat(),
        "mode": "paper",
        "state_source": state_source,
        "equity": {
            "current_equity": round(current_equity, 2),
            "initial_equity": INITIAL_EQUITY,
            "pnl": round(pnl_value, 2),
            "pnl_pct": round(pnl_pct, 6),
            "drawdown": round(drawdown, 6),
            "cash": equity_snapshot.get("cash"),
            "market_value": equity_snapshot.get("market_value"),
            "rolling_high": equity_snapshot.get("rolling_high"),
        },
        "exposure": {
            "risky_weight": round(float(risky["paper_weight"].sum()), 6) if not risky.empty else 0.0,
            "cash_weight": round(float(cash["paper_weight"].sum()), 6) if not cash.empty else 0.0,
            "reserved_cash_weight": round(float(reserved["paper_weight"].sum()), 6) if not reserved.empty else 0.0,
            "gross_exposure": round(float(risky["paper_weight"].abs().sum()), 6) if not risky.empty else 0.0,
            "net_exposure": round(float(risky["paper_weight"].sum()), 6) if not risky.empty else 0.0,
        },
        "decision": {
            "direction": risk_decision.get("final_direction"),
            "confidence": risk_decision.get("final_confidence"),
            "target_net_exposure": risk_decision.get("target_net_exposure"),
            "risk_label": risk_decision.get("risk_label"),
        },
        "holdings": pf.to_dict("records"),
        "pending_orders": pending_orders,
        "ledger_tail": ledger_rows[-25:],
        "counts": {
            "holding_count": int(len(pf)),
            "risky_position_count": int(len(risky)),
            "pending_order_count": int(len(pending_orders)),
            "ledger_row_count": int(len(ledger_rows)),
        },
    }


def portfolio_from_mtm(mtm_positions: pd.DataFrame, mtm_report: dict) -> pd.DataFrame:
    positions = mtm_positions.copy()
    rows = []

    for _, row in positions.iterrows():
        asset = row.get("asset")
        market_value = float(row.get("market_value") or 0.0)
        portfolio_weight = float(row.get("portfolio_weight") or 0.0)

        rows.append({
            "asset": asset,
            "paper_weight": round(portfolio_weight, 6),
            "paper_value": round(market_value, 2),
            "side": row.get("side"),
            "cost_drag": 0.0,
            "status": "OPEN_FROM_MARK_TO_MARKET",
            "quantity": row.get("quantity"),
            "avg_entry_price": row.get("avg_entry_price"),
            "current_price": row.get("current_price"),
            "cost_basis": row.get("cost_basis"),
            "unrealized_pnl": row.get("unrealized_pnl"),
            "unrealized_pnl_pct": row.get("unrealized_pnl_pct"),
        })

    equity = mtm_report.get("equity_snapshot", {}) or {}
    cash_value = float(equity.get("cash") or 0.0)
    current_equity = float(equity.get("equity") or INITIAL_EQUITY)
    cash_weight = cash_value / current_equity if current_equity else 0.0

    rows.append({
        "asset": "CASH",
        "paper_weight": round(cash_weight, 6),
        "paper_value": round(cash_value, 2),
        "side": "CASH",
        "cost_drag": 0.0,
        "status": "AVAILABLE_CASH_FROM_MTM",
    })

    return pd.DataFrame(rows)


def portfolio_from_broker_fills(fills: pd.DataFrame, broker_orders: pd.DataFrame | None = None) -> pd.DataFrame:
    df = fills.copy()
    df["filled_weight"] = pd.to_numeric(df.get("filled_weight", 0.0), errors="coerce").fillna(0.0)
    filled = df[df["fill_status"] == "PAPER_FILLED"].copy()

    rows = []

    if not filled.empty:
        grouped = filled.groupby(["asset", "side"], as_index=False)["filled_weight"].sum()

        for _, row in grouped.iterrows():
            weight = float(row["filled_weight"])
            rows.append({
                "asset": row["asset"],
                "paper_weight": round(weight, 6),
                "paper_value": round(INITIAL_EQUITY * weight, 2),
                "side": row["side"],
                "cost_drag": 0.0,
                "status": "OPEN_FROM_PAPER_BROKER_FILL",
            })

    risky_weight = sum(float(r["paper_weight"]) for r in rows if r["asset"] != "CASH")
    cash_weight = max(0.0, 1.0 - risky_weight)

    rows.append({
        "asset": "CASH",
        "paper_weight": round(cash_weight, 6),
        "paper_value": round(INITIAL_EQUITY * cash_weight, 2),
        "side": "CASH",
        "cost_drag": 0.0,
        "status": "AVAILABLE_CASH",
    })

    return pd.DataFrame(rows)


def empty_state() -> dict[str, Any]:
    return {
        "success": False,
        "timestamp": datetime.now(UTC).isoformat(),
        "mode": "paper",
        "error": "No MTM positions or broker fills available.",
        "equity": {},
        "exposure": {},
        "holdings": [],
        "pending_orders": [],
        "ledger_tail": [],
        "counts": {},
    }
