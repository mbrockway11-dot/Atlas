
"""Cost basis model."""

from __future__ import annotations

import pandas as pd


INITIAL_EQUITY = 100000.0


def build_cost_basis(fills: pd.DataFrame, prices: dict[str, float]) -> pd.DataFrame:
    if fills.empty:
        return pd.DataFrame()

    df = fills.copy()
    df = df[df["fill_status"] == "PAPER_FILLED"].copy()

    if df.empty:
        return pd.DataFrame()

    df["filled_weight"] = pd.to_numeric(df["filled_weight"], errors="coerce").fillna(0.0)

    rows = []

    for _, row in df.iterrows():
        asset = str(row.get("asset"))
        weight = float(row.get("filled_weight") or 0.0)
        current_price = float(prices.get(asset) or 1.0)

        notional = INITIAL_EQUITY * weight
        quantity = notional / current_price if current_price else 0.0

        rows.append({
            "asset": asset,
            "side": row.get("side"),
            "action": row.get("action"),
            "entry_price": current_price,
            "current_price": current_price,
            "quantity": quantity,
            "cost_basis": notional,
            "weight": weight,
            "source_fill": row.get("idempotency_key"),
            "filled_at": row.get("filled_at"),
        })

    basis = pd.DataFrame(rows)

    if basis.empty:
        return basis

    grouped = basis.groupby(["asset", "side"], as_index=False).agg({
        "quantity": "sum",
        "cost_basis": "sum",
        "weight": "sum",
        "current_price": "last",
    })

    grouped["avg_entry_price"] = grouped["cost_basis"] / grouped["quantity"].replace(0, pd.NA)
    grouped["avg_entry_price"] = grouped["avg_entry_price"].fillna(0.0)

    return grouped
