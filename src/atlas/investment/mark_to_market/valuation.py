
"""Mark-to-Market v4 valuation.

Cash and open positions come exclusively from Broker Ledger v4.1.
"""

from __future__ import annotations

import pandas as pd


DEFAULT_INITIAL_EQUITY = 100000.0


def value_ledger_positions(
    ledger_positions: pd.DataFrame,
    prices: dict[str, float],
    ledger_equity: float,
) -> pd.DataFrame:
    columns = [
        "asset",
        "side",
        "quantity",
        "cost_basis",
        "weight",
        "current_price",
        "avg_entry_price",
        "market_value",
        "portfolio_weight",
        "unrealized_pnl",
        "unrealized_pnl_pct",
        "source",
    ]

    if ledger_positions is None or ledger_positions.empty:
        return pd.DataFrame(columns=columns)

    rows = []

    for _, row in ledger_positions.iterrows():
        status = str(row.get("status") or "OPEN").upper()

        if status == "CLOSED":
            continue

        asset = str(row.get("asset") or "").strip()

        if not asset or asset.upper() == "CASH":
            continue

        side = str(row.get("side") or "LONG").upper()
        weight = number(row.get("net_weight"))
        cost_basis = number(row.get("market_value"))
        current_price = number(prices.get(asset))

        if current_price <= 0:
            current_price = 1.0

        # Broker Ledger v4.1 currently stores authoritative position
        # notional rather than units. Seed quantity from that snapshot.
        quantity = cost_basis / current_price if current_price else 0.0
        avg_entry_price = (
            cost_basis / quantity
            if quantity
            else current_price
        )

        market_value = quantity * current_price

        if side == "SHORT":
            unrealized_pnl = cost_basis - market_value
        else:
            unrealized_pnl = market_value - cost_basis

        unrealized_pnl_pct = (
            unrealized_pnl / cost_basis
            if cost_basis
            else 0.0
        )

        portfolio_weight = (
            market_value / ledger_equity
            if ledger_equity
            else 0.0
        )

        rows.append({
            "asset": asset,
            "side": side,
            "quantity": quantity,
            "cost_basis": cost_basis,
            "weight": weight,
            "current_price": current_price,
            "avg_entry_price": avg_entry_price,
            "market_value": market_value,
            "portfolio_weight": portfolio_weight,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_pct": unrealized_pnl_pct,
            "source": "broker_ledger_v4_1",
        })

    return pd.DataFrame(rows, columns=columns)


def ledger_cash(ledger_report: dict) -> float:
    return round(
        number(ledger_report.get("cash")),
        2,
    )


def ledger_equity(ledger_report: dict) -> float:
    equity = number(ledger_report.get("equity"))

    if equity > 0:
        return equity

    return DEFAULT_INITIAL_EQUITY


def number(value) -> float:
    try:
        if value is None or pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0
