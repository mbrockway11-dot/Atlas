
"""Rebalancing turnover controls."""

from __future__ import annotations

import pandas as pd


MIN_TRADE_DELTA = 0.01
MAX_TOTAL_TURNOVER = 0.25


def apply_turnover_controls(rebalance: pd.DataFrame) -> pd.DataFrame:
    if rebalance.empty:
        return rebalance

    out = rebalance.copy()
    out["abs_delta"] = out["delta_weight"].abs()
    out["trade_required"] = out["abs_delta"] >= MIN_TRADE_DELTA

    total_turnover = float(out.loc[out["asset"] != "CASH", "abs_delta"].sum())

    if total_turnover > MAX_TOTAL_TURNOVER:
        scale = MAX_TOTAL_TURNOVER / total_turnover
    else:
        scale = 1.0

    out["controlled_delta_weight"] = out["delta_weight"]

    mask = (out["asset"] != "CASH") & out["trade_required"]
    out.loc[mask, "controlled_delta_weight"] = out.loc[mask, "delta_weight"] * scale
    out.loc[~out["trade_required"], "controlled_delta_weight"] = 0.0

    out["turnover_scale"] = scale
    out["turnover_limited"] = total_turnover > MAX_TOTAL_TURNOVER

    return out
