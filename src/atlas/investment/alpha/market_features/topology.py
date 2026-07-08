
"""Market topology features."""

from __future__ import annotations

import pandas as pd


def build_topology_features(df: pd.DataFrame, *, window: int = 72, corr_threshold: float = 0.50) -> pd.DataFrame:
    """Build simple rolling correlation topology features."""
    if df.empty or "return_1" not in df.columns:
        return pd.DataFrame()

    pivot = df.pivot_table(index="date", columns="asset", values="return_1").sort_index()
    rows = []

    for idx in range(window, len(pivot)):
        date = pivot.index[idx]
        chunk = pivot.iloc[idx - window:idx]
        corr = chunk.corr()

        values = []
        edges = 0
        possible = 0

        assets = list(corr.columns)

        for i, left in enumerate(assets):
            for right in assets[i + 1:]:
                value = corr.loc[left, right]
                if pd.isna(value):
                    continue

                possible += 1
                values.append(float(value))

                if abs(value) >= corr_threshold:
                    edges += 1

        avg_corr = sum(values) / len(values) if values else None
        density = edges / possible if possible else None

        rows.append(
            {
                "date": date,
                "topology_window": window,
                "corr_threshold": corr_threshold,
                "avg_abs_corr": abs(avg_corr) if avg_corr is not None else None,
                "avg_corr": avg_corr,
                "edge_count": edges,
                "possible_edges": possible,
                "graph_density": density,
            }
        )

    return pd.DataFrame(rows)
