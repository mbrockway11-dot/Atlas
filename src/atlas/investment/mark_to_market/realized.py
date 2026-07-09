
"""Realized PnL placeholder."""

from __future__ import annotations

import pandas as pd


def realized_pnl() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "asset",
        "side",
        "realized_pnl",
        "realized_pnl_pct",
        "closed_at",
        "reason",
    ])
