
"""Asset leadership features."""

from __future__ import annotations

import pandas as pd


def build_leadership_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build leader/laggard features per timestamp."""
    if df.empty:
        return pd.DataFrame()

    rows = []

    for date, group in df.groupby("date"):
        row = {"date": date}

        for window in [24, 72, 288]:
            col = f"return_{window}"
            if col not in group.columns:
                continue

            g = group.dropna(subset=[col])
            if g.empty:
                continue

            leader = g.sort_values(col, ascending=False).iloc[0]
            laggard = g.sort_values(col, ascending=True).iloc[0]

            row[f"leader_asset_{window}"] = leader["asset"]
            row[f"leader_return_{window}"] = float(leader[col])
            row[f"laggard_asset_{window}"] = laggard["asset"]
            row[f"laggard_return_{window}"] = float(laggard[col])
            row[f"leader_laggard_spread_{window}"] = float(leader[col] - laggard[col])

        rows.append(row)

    out = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)

    for window in [24, 72, 288]:
        leader_col = f"leader_asset_{window}"
        if leader_col in out.columns:
            out[f"leader_changed_{window}"] = (out[leader_col] != out[leader_col].shift(1)).astype(int)
            out[f"leader_persistence_{window}"] = persistence_run_length(out[leader_col])

    return out


def persistence_run_length(series: pd.Series) -> list[int]:
    """Calculate consecutive persistence length."""
    values = []
    current = None
    count = 0

    for value in series:
        if value == current:
            count += 1
        else:
            current = value
            count = 1
        values.append(count)

    return values
