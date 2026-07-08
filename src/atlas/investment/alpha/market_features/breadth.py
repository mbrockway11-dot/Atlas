
"""Cross-sectional breadth features."""

from __future__ import annotations

import pandas as pd


def build_breadth_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build market-wide breadth per timestamp."""
    if df.empty:
        return pd.DataFrame()

    rows = []

    for date, group in df.groupby("date"):
        row = {"date": date, "asset_count": int(group["asset"].nunique())}

        for window in [1, 4, 12, 24, 72, 288]:
            col = f"return_{window}"
            if col not in group.columns:
                continue

            s = pd.to_numeric(group[col], errors="coerce").dropna()
            if s.empty:
                continue

            row[f"breadth_positive_{window}"] = float((s > 0).mean())
            row[f"median_return_{window}"] = float(s.median())
            row[f"mean_return_{window}"] = float(s.mean())
            row[f"dispersion_{window}"] = float(s.std())
            row[f"max_return_{window}"] = float(s.max())
            row[f"min_return_{window}"] = float(s.min())
            row[f"spread_return_{window}"] = float(s.max() - s.min())

        rows.append(row)

    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
