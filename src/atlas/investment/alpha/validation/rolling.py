
"""Rolling-window validation."""

from __future__ import annotations

from typing import Any

import pandas as pd


def rolling_window_validation(trades: pd.DataFrame, *, window_days: int = 180) -> dict[str, Any]:
    if trades.empty:
        return {"success": False, "windows": [], "stability_score": 0.0}

    df = trades.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["return"] = pd.to_numeric(df["return"], errors="coerce")
    df = df.dropna(subset=["date", "return"]).sort_values("date")

    if df.empty:
        return {"success": False, "windows": [], "stability_score": 0.0}

    start = df["date"].min()
    end = df["date"].max()
    windows = []

    current = start
    while current <= end:
        window_end = current + pd.Timedelta(days=window_days)
        chunk = df[(df["date"] >= current) & (df["date"] < window_end)]

        if not chunk.empty:
            windows.append({
                "start": str(current),
                "end": str(window_end),
                "trade_count": int(len(chunk)),
                "win_rate": round(float((chunk["return"] > 0).mean()), 6),
                "avg_return": round(float(chunk["return"].mean()), 8),
                "median_return": round(float(chunk["return"].median()), 8),
            })

        current = current + pd.Timedelta(days=window_days)

    positive = [w for w in windows if w["avg_return"] > 0 and w["trade_count"] >= 3]
    stability = len(positive) / len(windows) if windows else 0.0

    return {
        "success": True,
        "window_days": window_days,
        "window_count": len(windows),
        "positive_window_count": len(positive),
        "stability_score": round(float(stability), 6),
        "windows": windows,
    }
