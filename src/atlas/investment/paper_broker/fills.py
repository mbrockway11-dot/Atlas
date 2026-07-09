
"""Paper Broker v3 fill normalization."""

from __future__ import annotations

from datetime import datetime, UTC
import pandas as pd


INITIAL_EQUITY = 100000.0


def normalize_execution_fills(new_fills: pd.DataFrame) -> list[dict]:
    if new_fills.empty:
        return []

    rows = []

    for _, row in new_fills.iterrows():
        fill_status = str(row.get("fill_status") or "").upper()
        execution_status = str(row.get("execution_status") or "").upper()

        if fill_status not in {"FILLED_SIMULATED", "PAPER_FILLED"} and execution_status not in {"EXECUTED_SIMULATED"}:
            continue

        asset = str(row.get("asset"))
        side = str(row.get("side") or "LONG")
        action = str(row.get("action") or row.get("order_action") or "BUY").upper()
        filled_weight = float(row.get("filled_weight") or row.get("requested_weight") or 0.0)

        if filled_weight <= 0:
            continue

        stable_key = row.get("stable_order_key") or row.get("idempotency_key")

        rows.append({
            "broker_fill_id": f"paper::{stable_key}",
            "filled_at": row.get("fill_timestamp") or datetime.now(UTC).isoformat(),
            "execution_batch_id": row.get("execution_batch_id"),
            "execution_id": row.get("execution_id"),
            "stable_order_key": stable_key,
            "idempotency_key": stable_key,
            "asset": asset,
            "side": side,
            "action": action,
            "requested_weight": row.get("requested_weight"),
            "filled_weight": round(filled_weight, 6),
            "notional_value": round(INITIAL_EQUITY * filled_weight, 2),
            "fill_status": "PAPER_FILLED",
            "broker": "paper_broker_v3",
            "route": row.get("broker_route") or "paper",
            "risk_label": row.get("risk_label"),
            "safety_status": row.get("safety_status"),
            "fee_drag": row.get("fee_drag", 0.0),
            "slippage_drag": row.get("slippage_drag", 0.0),
            "total_cost_drag": row.get("total_cost_drag", 0.0),
            "notes": "Paper Broker v3 consumed Execution Engine v3 fill.",
        })

    return rows


# Backward compatibility
def build_paper_fills(new_orders: pd.DataFrame) -> list[dict]:
    return normalize_execution_fills(new_orders)
