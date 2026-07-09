
"""Paper Broker fill simulation."""

from __future__ import annotations

from datetime import datetime, UTC

import pandas as pd

from atlas.investment.paper_broker.idempotency import target_key


def simulate_paper_broker_fills(orders: pd.DataFrame) -> pd.DataFrame:
    if orders.empty:
        return pd.DataFrame()

    now = datetime.now(UTC).isoformat()
    rows = []

    for _, row in orders.iterrows():
        status = str(row.get("execution_status") or "").upper()

        if status != "APPROVED_FOR_EXECUTION":
            continue

        weight = float(row.get("weight") or 0.0)
        asset = str(row.get("asset"))
        side = str(row.get("side"))
        action = str(row.get("action"))

        rows.append({
            "filled_at": now,
            "execution_batch_id": row.get("execution_batch_id"),
            "idempotency_key": row.get("idempotency_key"),
            "target_key": row.get("target_key") or target_key(asset, side, action, weight),
            "asset": asset,
            "side": side,
            "action": action,
            "requested_weight": weight,
            "filled_weight": weight,
            "fill_status": "PAPER_FILLED",
            "broker": "paper",
            "route": row.get("route"),
            "risk_label": row.get("risk_label"),
            "safety_approved": row.get("safety_approved"),
            "notes": "Paper Broker v2 target-idempotent simulated fill.",
        })

    return pd.DataFrame(rows)
