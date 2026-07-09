
"""Portfolio State builder."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

import pandas as pd


INITIAL_EQUITY = 100000.0


def build_portfolio_state(inputs: dict[str, Any]) -> dict[str, Any]:
    fills = inputs.get("paper_broker_fills")
    portfolio = inputs.get("paper_portfolio")
    ledger = inputs.get("paper_broker_ledger")
    legacy_ledger = inputs.get("paper_ledger")
    broker_orders = inputs.get("broker_orders")
    performance = inputs.get("performance", {}) or {}
    decision = inputs.get("decision", {}) or {}

    if fills is not None and not fills.empty:
        pf = portfolio_from_broker_fills(fills, broker_orders)
        state_source = "paper_broker_v2"
    elif portfolio is not None and not portfolio.empty:
        pf = portfolio.copy()
        state_source = "legacy_paper_trading"
    else:
        return empty_state()

    pf["paper_weight"] = pd.to_numeric(pf.get("paper_weight", 0.0), errors="coerce").fillna(0.0)
    pf["paper_value"] = pd.to_numeric(pf.get("paper_value", 0.0), errors="coerce").fillna(0.0)

    risky = pf[~pf["asset"].isin(["CASH", "RESERVED_CASH"])]
    cash = pf[pf["asset"] == "CASH"]
    reserved = pf[pf["asset"] == "RESERVED_CASH"]

    holdings = pf.to_dict("records")
    pending_orders = broker_orders.to_dict("records") if broker_orders is not None and not broker_orders.empty else []

    if ledger is not None and not ledger.empty:
        ledger_rows = ledger.to_dict("records")
    elif legacy_ledger is not None and not legacy_ledger.empty:
        ledger_rows = legacy_ledger.to_dict("records")
    else:
        ledger_rows = []

    pnl = performance.get("pnl", {}) or {}
    risk_decision = decision.get("risk_adjusted_decision", {}) or {}

    current_equity = round(float(pf["paper_value"].sum()), 2)
    pnl_value = round(current_equity - INITIAL_EQUITY, 2)
    pnl_pct = round(pnl_value / INITIAL_EQUITY, 6)

    state = {
        "success": True,
        "timestamp": datetime.now(UTC).isoformat(),
        "mode": "paper",
        "state_source": state_source,
        "equity": {
            "current_equity": current_equity,
            "initial_equity": pnl.get("initial_equity", INITIAL_EQUITY),
            "pnl": pnl_value,
            "pnl_pct": pnl_pct,
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
        "holdings": holdings,
        "pending_orders": pending_orders,
        "ledger_tail": ledger_rows[-25:],
        "counts": {
            "holding_count": int(len(pf)),
            "risky_position_count": int(len(risky)),
            "pending_order_count": int(len(pending_orders)),
            "ledger_row_count": int(len(ledger_rows)),
        },
    }

    return state


def portfolio_from_broker_fills(fills: pd.DataFrame, broker_orders: pd.DataFrame | None = None) -> pd.DataFrame:
    df = fills.copy()

    df["filled_weight"] = pd.to_numeric(df.get("filled_weight", 0.0), errors="coerce").fillna(0.0)

    filled = df[df["fill_status"] == "PAPER_FILLED"].copy()

    rows = []

    if not filled.empty:
        grouped = (
            filled
            .groupby(["asset", "side"], as_index=False)["filled_weight"]
            .sum()
        )

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

    pending_weight = pending_unfilled_weight(broker_orders, fills)

    if pending_weight > 0:
        rows.append({
            "asset": "RESERVED_CASH",
            "paper_weight": round(pending_weight, 6),
            "paper_value": round(INITIAL_EQUITY * pending_weight, 2),
            "side": "CASH",
            "cost_drag": 0.0,
            "status": "PENDING_EXECUTION_RESERVE",
        })

    cash_weight = max(0.0, 1.0 - risky_weight - pending_weight)

    rows.append({
        "asset": "CASH",
        "paper_weight": round(cash_weight, 6),
        "paper_value": round(INITIAL_EQUITY * cash_weight, 2),
        "side": "CASH",
        "cost_drag": 0.0,
        "status": "AVAILABLE_CASH",
    })

    return pd.DataFrame(rows)


def pending_unfilled_weight(broker_orders: pd.DataFrame | None, fills: pd.DataFrame) -> float:
    if broker_orders is None or broker_orders.empty:
        return 0.0

    if "asset" not in broker_orders.columns or "weight" not in broker_orders.columns:
        return 0.0

    filled_keys = set()
    if not fills.empty and "asset" in fills.columns:
        filled_keys = set(fills["asset"].astype(str).tolist())

    pending = broker_orders[~broker_orders["asset"].astype(str).isin(filled_keys)].copy()

    if pending.empty:
        return 0.0

    pending["weight"] = pd.to_numeric(pending["weight"], errors="coerce").fillna(0.0)

    return float(pending["weight"].sum())


def empty_state() -> dict[str, Any]:
    return {
        "success": False,
        "timestamp": datetime.now(UTC).isoformat(),
        "mode": "paper",
        "error": "No paper portfolio or broker fills available.",
        "equity": {},
        "exposure": {},
        "holdings": [],
        "pending_orders": [],
        "ledger_tail": [],
        "counts": {},
    }
