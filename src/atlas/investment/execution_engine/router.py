
"""Execution routing."""

from __future__ import annotations

import pandas as pd


def route_orders(orders: pd.DataFrame, *, mode: str = "paper") -> pd.DataFrame:
    if orders.empty:
        return pd.DataFrame()

    out = orders.copy()
    out["execution_mode"] = mode
    out["route"] = out["broker"].apply(lambda b: route_for_broker(str(b), mode))
    out["route_status"] = "ROUTED"

    return out


def route_for_broker(broker: str, mode: str) -> str:
    b = broker.lower()

    if mode != "live":
        return "paper_execution_route"

    if b == "phantom":
        return "phantom_wallet_route"

    if b == "jupiter":
        return "jupiter_route"

    if b == "paper":
        return "paper_execution_route"

    return "unknown_route"
