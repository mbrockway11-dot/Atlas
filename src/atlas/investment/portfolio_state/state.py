
"""Portfolio State builder."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

import pandas as pd


def build_portfolio_state(inputs: dict[str, Any]) -> dict[str, Any]:
    portfolio = inputs.get("paper_portfolio")
    ledger = inputs.get("paper_ledger")
    broker_orders = inputs.get("broker_orders")
    performance = inputs.get("performance", {}) or {}
    decision = inputs.get("decision", {}) or {}

    if portfolio is None or portfolio.empty:
        return empty_state()

    pf = portfolio.copy()
    pf["paper_weight"] = pd.to_numeric(pf.get("paper_weight", 0.0), errors="coerce").fillna(0.0)
    pf["paper_value"] = pd.to_numeric(pf.get("paper_value", 0.0), errors="coerce").fillna(0.0)

    risky = pf[~pf["asset"].isin(["CASH", "RESERVED_CASH"])]
    cash = pf[pf["asset"] == "CASH"]
    reserved = pf[pf["asset"] == "RESERVED_CASH"]

    holdings = pf.to_dict("records")
    pending_orders = broker_orders.to_dict("records") if broker_orders is not None and not broker_orders.empty else []
    ledger_rows = ledger.to_dict("records") if ledger is not None and not ledger.empty else []

    pnl = performance.get("pnl", {}) or {}
    risk_decision = decision.get("risk_adjusted_decision", {}) or {}

    state = {
        "success": True,
        "timestamp": datetime.now(UTC).isoformat(),
        "mode": "paper",
        "equity": {
            "current_equity": round(float(pf["paper_value"].sum()), 2),
            "initial_equity": pnl.get("initial_equity"),
            "pnl": pnl.get("pnl"),
            "pnl_pct": pnl.get("pnl_pct"),
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


def empty_state() -> dict[str, Any]:
    return {
        "success": False,
        "timestamp": datetime.now(UTC).isoformat(),
        "mode": "paper",
        "error": "No paper portfolio available.",
        "equity": {},
        "exposure": {},
        "holdings": [],
        "pending_orders": [],
        "ledger_tail": [],
        "counts": {},
    }
