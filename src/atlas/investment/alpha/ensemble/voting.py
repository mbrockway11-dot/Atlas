
"""Alpha ensemble voting."""

from __future__ import annotations

from typing import Any

import pandas as pd


def build_strategy_votes(
    trades: pd.DataFrame,
    weights: dict[str, Any],
) -> pd.DataFrame:
    """Convert historical trades into weighted strategy votes."""
    if trades.empty:
        return pd.DataFrame()

    weight_map = {
        row["hypothesis_id"]: row["weight"]
        for row in weights.get("weights", [])
    }

    promoted_ids = set(weight_map)

    df = trades[trades["hypothesis_id"].isin(promoted_ids)].copy()

    if df.empty:
        return pd.DataFrame()

    df["vote"] = df.get("direction", "LONG").fillna("LONG").astype(str).str.upper()
    df["weight"] = df["hypothesis_id"].map(weight_map).fillna(0.0)

    return df


def aggregate_votes(votes: pd.DataFrame) -> pd.DataFrame:
    """Aggregate votes per date and asset."""
    if votes.empty:
        return pd.DataFrame()

    rows = []

    for (date, asset), group in votes.groupby(["date", "asset"], dropna=False):
        long_weight = float(group.loc[group["vote"] == "LONG", "weight"].sum())
        short_weight = float(group.loc[group["vote"] == "SHORT", "weight"].sum())
        total_weight = float(group["weight"].sum())

        rows.append(
            {
                "date": date,
                "asset": asset,
                "long_weight": long_weight,
                "short_weight": short_weight,
                "total_weight": total_weight,
                "net_long_score": long_weight - short_weight,
                "strategy_count": int(group["hypothesis_id"].nunique()),
                "active_strategies": sorted(group["hypothesis_id"].dropna().unique().tolist()),
            }
        )

    out = pd.DataFrame(rows).sort_values(["date", "net_long_score"], ascending=[True, False])
    return out.reset_index(drop=True)
