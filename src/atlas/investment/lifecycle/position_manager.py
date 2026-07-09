
"""Portfolio Lifecycle v2 position construction."""

from __future__ import annotations

from datetime import datetime, UTC

import pandas as pd

from atlas.investment.lifecycle.transition import transition_for_position


def build_lifecycle_rows(inputs: dict) -> list[dict]:
    mtm = inputs.get("mtm_positions")
    fills = inputs.get("paper_broker_fills")
    action_engine = inputs.get("action_engine", {}) or {}

    action_lookup = {
        row.get("position_id"): row
        for row in action_engine.get("actions", []) or []
    }

    rows = []

    if mtm is None or mtm.empty:
        return rows

    fill_lookup = build_fill_lookup(fills)

    for _, pos in mtm.iterrows():
        position = pos.to_dict()

        asset = str(position.get("asset"))
        side = str(position.get("side") or "LONG")
        position_id = f"paper::{asset}::{side}"

        state, reason = transition_for_position(position, action_lookup)

        fill = fill_lookup.get(asset, {})

        rows.append({
            "position_id": position_id,
            "asset": asset,
            "side": side,
            "state": state,
            "entry_timestamp": fill.get("filled_at"),
            "entry_price": position.get("avg_entry_price"),
            "current_price": position.get("current_price"),
            "quantity": position.get("quantity"),
            "cost_basis": position.get("cost_basis"),
            "market_value": position.get("market_value"),
            "portfolio_weight": position.get("portfolio_weight"),
            "unrealized_pnl": position.get("unrealized_pnl"),
            "unrealized_pnl_pct": position.get("unrealized_pnl_pct"),
            "holding_age_hours": holding_age_hours(fill.get("filled_at")),
            "transition_reason": reason,
            "updated_at": datetime.now(UTC).isoformat(),
        })

    rows.append({
        "position_id": "cash::CASH",
        "asset": "CASH",
        "side": "CASH",
        "state": "CASH",
        "transition_reason": "Cash reserve.",
        "updated_at": datetime.now(UTC).isoformat(),
    })

    return rows


def build_fill_lookup(fills: pd.DataFrame | None) -> dict[str, dict]:
    if fills is None or fills.empty or "asset" not in fills.columns:
        return {}

    out = {}

    for _, row in fills.iterrows():
        asset = str(row.get("asset"))
        if asset not in out:
            out[asset] = row.to_dict()

    return out


def holding_age_hours(filled_at: str | None) -> float | None:
    if not filled_at:
        return None

    try:
        filled = pd.to_datetime(filled_at, utc=True)
        now = pd.Timestamp.utcnow()
        return round((now - filled).total_seconds() / 3600, 4)
    except Exception:
        return None
