
"""Turnover calculations."""

from __future__ import annotations


MIN_DELTA = 0.005


def build_rebalance_table(current: dict[str, float], optimized: dict[str, float]) -> list[dict]:
    assets = sorted(set(current) | set(optimized))
    rows = []

    for asset in assets:
        cw = float(current.get(asset, 0.0))
        tw = float(optimized.get(asset, 0.0))
        delta = round(tw - cw, 6)

        if abs(delta) < MIN_DELTA:
            action = "HOLD"
        elif delta > 0:
            action = "BUY"
        else:
            action = "SELL"

        rows.append({
            "asset": asset,
            "current_weight": round(cw, 6),
            "target_weight": round(tw, 6),
            "signed_delta": delta,
            "abs_delta": round(abs(delta), 6),
            "rebalance_action": action,
            "reason": "Optimize current MTM portfolio toward risk-adjusted target portfolio.",
        })

    return rows


def total_turnover(rows: list[dict]) -> float:
    return round(sum(float(r.get("abs_delta") or 0.0) for r in rows if r.get("rebalance_action") != "HOLD"), 6)
