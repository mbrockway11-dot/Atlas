
"""Mark-to-Market v3 valuation."""

from __future__ import annotations

import pandas as pd


INITIAL_EQUITY = 100000.0


def value_positions(broker_positions: pd.DataFrame, broker_fills: pd.DataFrame, prices: dict[str, float]) -> pd.DataFrame:
    if broker_positions.empty:
        return pd.DataFrame(columns=[
            "asset", "side", "quantity", "cost_basis", "weight", "current_price",
            "avg_entry_price", "market_value", "portfolio_weight",
            "unrealized_pnl", "unrealized_pnl_pct"
        ])

    rows = []

    for _, row in broker_positions.iterrows():
        asset = str(row.get("asset"))
        side = str(row.get("side") or "LONG")
        net_weight = float(row.get("net_weight") or 0.0)
        cost_basis = float(row.get("notional_value") or (INITIAL_EQUITY * net_weight))
        current_price = float(prices.get(asset, 1.0))

        avg_entry_price = average_entry_price(asset, broker_fills, current_price)
        quantity = cost_basis / avg_entry_price if avg_entry_price else 0.0
        market_value = quantity * current_price

        unrealized = market_value - cost_basis
        unrealized_pct = unrealized / cost_basis if cost_basis else 0.0

        rows.append({
            "asset": asset,
            "side": side,
            "quantity": quantity,
            "cost_basis": cost_basis,
            "weight": net_weight,
            "current_price": current_price,
            "avg_entry_price": avg_entry_price,
            "market_value": market_value,
            "portfolio_weight": market_value / INITIAL_EQUITY if INITIAL_EQUITY else 0.0,
            "unrealized_pnl": unrealized,
            "unrealized_pnl_pct": unrealized_pct,
        })

    return pd.DataFrame(rows)


def average_entry_price(asset: str, fills: pd.DataFrame, fallback_price: float) -> float:
    if fills.empty or "asset" not in fills.columns:
        return fallback_price

    df = fills[fills["asset"].astype(str) == asset].copy()

    if df.empty:
        return fallback_price

    # Broker v3 currently stores notional/weight but not explicit execution price.
    # Until Paper Broker v4 stores prices, use current price as neutral entry basis.
    return fallback_price


def cash_value(cash_ledger: pd.DataFrame, positions: pd.DataFrame) -> float:
    if not cash_ledger.empty and "cash_delta" in cash_ledger.columns:
        delta = pd.to_numeric(cash_ledger["cash_delta"], errors="coerce").fillna(0.0).sum()
        return round(INITIAL_EQUITY + float(delta), 2)

    market_value = 0.0
    if not positions.empty and "market_value" in positions.columns:
        market_value = pd.to_numeric(positions["market_value"], errors="coerce").fillna(0.0).sum()

    return round(INITIAL_EQUITY - float(market_value), 2)
