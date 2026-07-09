
"""Portfolio lifecycle transitions."""

from __future__ import annotations

from datetime import datetime, UTC
import pandas as pd

from atlas.investment.lifecycle import states


def build_lifecycle_rows(
    holdings: pd.DataFrame,
    broker_orders: pd.DataFrame,
    existing: pd.DataFrame,
) -> pd.DataFrame:
    """Build/update lifecycle state from holdings and broker orders."""
    now = datetime.now(UTC).isoformat()

    rows = []

    existing_keys = set()
    if existing is not None and not existing.empty and "position_id" in existing.columns:
        existing_keys = set(existing["position_id"].astype(str).tolist())

    # Existing holdings become OPEN / CASH / RESERVED states.
    if holdings is not None and not holdings.empty:
        for _, row in holdings.iterrows():
            asset = str(row.get("asset"))
            side = str(row.get("side", "UNKNOWN"))
            position_id = f"paper::{asset}::{side}"

            if asset == "CASH":
                state = states.CASH
            elif asset == "RESERVED_CASH":
                state = states.RESERVED
            else:
                state = states.OPEN

            rows.append({
                "position_id": position_id,
                "asset": asset,
                "side": side,
                "state": state,
                "weight": row.get("paper_weight"),
                "value": row.get("paper_value"),
                "opened_at": now if position_id not in existing_keys else previous_value(existing, position_id, "opened_at", now),
                "updated_at": now,
                "source": "paper_portfolio",
                "reason": row.get("status", "Imported from paper portfolio."),
            })

    # Broker orders become APPROVED / QUEUED if they are not yet in holdings.
    if broker_orders is not None and not broker_orders.empty:
        for _, row in broker_orders.iterrows():
            asset = str(row.get("asset"))
            side = str(row.get("side", "UNKNOWN"))
            action = str(row.get("action", "UNKNOWN"))
            position_id = f"broker::{asset}::{side}::{action}"

            rows.append({
                "position_id": position_id,
                "asset": asset,
                "side": side,
                "state": states.APPROVED,
                "weight": row.get("weight"),
                "value": None,
                "opened_at": now if position_id not in existing_keys else previous_value(existing, position_id, "opened_at", now),
                "updated_at": now,
                "source": "broker_interface",
                "reason": row.get("status", "Approved broker order."),
            })

    return pd.DataFrame(rows)


def previous_value(existing: pd.DataFrame, position_id: str, column: str, default):
    if existing is None or existing.empty:
        return default

    if column not in existing.columns or "position_id" not in existing.columns:
        return default

    matched = existing[existing["position_id"].astype(str) == str(position_id)]

    if matched.empty:
        return default

    value = matched.iloc[-1].get(column)
    return value if pd.notna(value) else default
