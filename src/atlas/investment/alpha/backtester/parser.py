
"""Alpha hypothesis rule parser."""

from __future__ import annotations

from typing import Any

import pandas as pd


OPS = {
    ">": lambda s, v: s > v,
    ">=": lambda s, v: s >= v,
    "<": lambda s, v: s < v,
    "<=": lambda s, v: s <= v,
    "==": lambda s, v: s == v,
    "!=": lambda s, v: s != v,
}


def apply_conditions(df: pd.DataFrame, conditions: list[dict[str, Any]]) -> pd.Series:
    """Apply hypothesis conditions to a dataframe."""
    if df.empty:
        return pd.Series(dtype=bool)

    mask = pd.Series(True, index=df.index)

    for cond in conditions:
        feature = cond.get("feature")
        op = cond.get("op")
        value = cond.get("value")

        if feature not in df.columns or op not in OPS:
            return pd.Series(False, index=df.index)

        series = df[feature]

        try:
            mask &= OPS[op](series, value)
        except Exception:
            return pd.Series(False, index=df.index)

    return mask.fillna(False)
