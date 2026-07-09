
"""Rebalance Engine v4 turnover controls."""

from __future__ import annotations


MAX_TURNOVER = 0.35


def controlled_turnover(rows: list[dict]) -> tuple[list[dict], float]:
    risky_rows = [r for r in rows if r.get("asset") != "CASH" and r.get("rebalance_action") in {"BUY", "SELL"}]
    turnover = round(sum(float(r.get("abs_delta") or 0.0) for r in risky_rows), 6)

    if turnover <= MAX_TURNOVER or turnover == 0:
        return rows, turnover

    scale = MAX_TURNOVER / turnover
    adjusted = []

    for row in rows:
        row = dict(row)

        if row.get("asset") != "CASH" and row.get("rebalance_action") in {"BUY", "SELL"}:
            row["signed_delta"] = round(float(row["signed_delta"]) * scale, 6)
            row["abs_delta"] = round(abs(float(row["signed_delta"])), 6)
            row["target_weight"] = round(float(row["current_weight"]) + float(row["signed_delta"]), 6)
            row["reason"] += " Turnover scaled to v4 cap."

        adjusted.append(row)

    new_turnover = round(sum(float(r.get("abs_delta") or 0.0) for r in adjusted if r.get("asset") != "CASH" and r.get("rebalance_action") in {"BUY", "SELL"}), 6)
    return adjusted, new_turnover
