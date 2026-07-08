
"""Execution sizing."""

from __future__ import annotations

import pandas as pd


def scale_portfolio_to_decision(portfolio: pd.DataFrame, decision: dict) -> pd.DataFrame:
    """Scale target portfolio weights by Decision Engine exposure."""
    if portfolio.empty:
        return pd.DataFrame()

    risk = decision.get("risk_adjusted_decision", {}) if decision else {}
    target_net = float(risk.get("target_net_exposure") or 0.0)
    direction = str(risk.get("final_direction") or "CASH").upper()

    df = portfolio.copy()
    df["target_weight"] = pd.to_numeric(df["target_weight"], errors="coerce").fillna(0.0)

    risky = df[df["asset"] != "CASH"].copy()
    cash = df[df["asset"] == "CASH"].copy()

    risky_sum = risky["target_weight"].sum()

    if risky_sum <= 0 or direction in {"CASH", "NEUTRAL"}:
        return pd.DataFrame([{
            "asset": "CASH",
            "planned_weight": 1.0,
            "side": "CASH",
            "action": "HOLD_CASH",
            "priority": 0,
            "reason": "Decision Engine selected cash/neutral or no risky portfolio.",
        }])

    scaled = []

    for _, row in risky.iterrows():
        normalized_weight = float(row["target_weight"]) / float(risky_sum)
        planned_weight = abs(target_net) * normalized_weight

        if direction == "LONG":
            side = "LONG"
            action = "BUY_OR_HOLD"
        elif direction == "SHORT":
            side = "SHORT"
            action = "SHORT_OR_HOLD"
        else:
            side = "CASH"
            action = "HOLD_CASH"

        scaled.append({
            "asset": row["asset"],
            "planned_weight": round(float(planned_weight), 6),
            "side": side,
            "action": action,
            "priority": int(row.get("rank") or 99),
            "alpha_score": row.get("alpha_score"),
            "rank_label": row.get("rank_label"),
            "reason": f"Scaled portfolio allocation to Decision Engine target exposure {target_net}.",
        })

    used = sum(x["planned_weight"] for x in scaled)
    scaled.append({
        "asset": "CASH",
        "planned_weight": round(float(max(0.0, 1.0 - used)), 6),
        "side": "CASH",
        "action": "HOLD_CASH",
        "priority": 999,
        "alpha_score": 0.0,
        "rank_label": "cash_reserve",
        "reason": "Residual cash after risk-adjusted execution sizing.",
    })

    return pd.DataFrame(scaled).sort_values(["priority", "asset"])
