
"""Paper broker adapter."""

from __future__ import annotations

import pandas as pd

from atlas.investment.broker.schema import BrokerOrder


def build_paper_broker_orders(orders: pd.DataFrame, safety: dict) -> list[BrokerOrder]:
    if not safety.get("approved"):
        return []

    if orders.empty:
        return []

    rows = []

    for _, row in orders.iterrows():
        action = str(row.get("order_action") or "NO_ORDER").upper()

        if action not in {"BUY", "SELL_SHORT"}:
            continue

        rows.append(BrokerOrder(
            asset=str(row.get("asset")),
            side=str(row.get("side")),
            action=action,
            weight=float(row.get("planned_weight") or 0.0),
            broker="paper",
            status="APPROVED_FOR_PAPER",
        ))

    return rows
