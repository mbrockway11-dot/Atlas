
"""Rebalancing optimizer."""

from __future__ import annotations

import pandas as pd


def current_weights_from_state(portfolio_state: dict) -> pd.DataFrame:
    state = portfolio_state.get("state", {}) or {}
    holdings = state.get("holdings", []) or []

    if not holdings:
        return pd.DataFrame(columns=["asset", "current_weight"])

    rows = []

    for row in holdings:
        asset = row.get("asset")
        if asset == "RESERVED_CASH":
            asset = "CASH"

        rows.append({
            "asset": asset,
            "current_weight": float(row.get("paper_weight") or 0.0),
        })

    df = pd.DataFrame(rows)
    return df.groupby("asset", as_index=False)["current_weight"].sum()


def target_weights_from_alpha(target_portfolio: pd.DataFrame, decision: dict) -> pd.DataFrame:
    if target_portfolio.empty:
        return pd.DataFrame(columns=["asset", "target_weight"])

    risk = decision.get("risk_adjusted_decision", {}) or {}
    target_exposure = abs(float(risk.get("target_net_exposure") or 0.0))

    df = target_portfolio.copy()

    if "target_weight" not in df.columns:
        return pd.DataFrame(columns=["asset", "target_weight"])

    df["target_weight"] = pd.to_numeric(df["target_weight"], errors="coerce").fillna(0.0)

    risky = df[df["asset"] != "CASH"].copy()

    risky_sum = float(risky["target_weight"].sum()) if not risky.empty else 0.0

    rows = []

    if risky_sum > 0:
        for _, row in risky.iterrows():
            rows.append({
                "asset": row.get("asset"),
                "target_weight": round(float(row["target_weight"]) / risky_sum * target_exposure, 6),
            })

    cash_weight = max(0.0, 1.0 - sum(r["target_weight"] for r in rows))
    rows.append({
        "asset": "CASH",
        "target_weight": round(float(cash_weight), 6),
    })

    return pd.DataFrame(rows)


def optimize_rebalance(current: pd.DataFrame, target: pd.DataFrame) -> pd.DataFrame:
    merged = pd.merge(current, target, on="asset", how="outer").fillna(0.0)
    merged["delta_weight"] = merged["target_weight"] - merged["current_weight"]

    return merged.sort_values("asset").reset_index(drop=True)
