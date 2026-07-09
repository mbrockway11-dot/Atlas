
"""Paper Broker ledger."""

from __future__ import annotations

import pandas as pd


def append_fills(existing: pd.DataFrame, new_fills: pd.DataFrame) -> pd.DataFrame:
    if existing.empty:
        return new_fills

    if new_fills.empty:
        return existing

    return pd.concat([existing, new_fills], ignore_index=True)
