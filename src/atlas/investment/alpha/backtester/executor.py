
"""Alpha hypothesis executor."""

from __future__ import annotations

from typing import Any

import pandas as pd

from atlas.investment.alpha.backtester.parser import apply_conditions


def execute_hypothesis(
    hypothesis: dict[str, Any],
    market_features: pd.DataFrame,
    asset_features: pd.DataFrame,
) -> pd.DataFrame:
    """Execute one hypothesis into trade candidates."""
    source = infer_condition_source(hypothesis)

    if source == "asset":
        return execute_asset_hypothesis(hypothesis, asset_features)

    return execute_market_hypothesis(hypothesis, market_features, asset_features)


def infer_condition_source(hypothesis: dict[str, Any]) -> str:
    """Infer whether rule is asset-level or market-level."""
    conditions = hypothesis.get("conditions", []) or []
    if any(c.get("source") == "asset" for c in conditions):
        return "asset"
    return "market"


def execute_asset_hypothesis(hypothesis: dict[str, Any], asset_features: pd.DataFrame) -> pd.DataFrame:
    """Execute asset-level hypothesis."""
    if asset_features.empty:
        return pd.DataFrame()

    conditions = hypothesis.get("conditions", []) or []
    mask = apply_conditions(asset_features, conditions)
    hits = asset_features.loc[mask].copy()

    if hits.empty:
        return pd.DataFrame()

    hold = int(hypothesis.get("hold_period", 72))
    future_col = f"future_return_{hold}"

    full_returns = asset_features[["date", "asset", "close"]].copy()
    full_returns = full_returns.sort_values(["asset", "date"])
    full_returns[future_col] = (
        full_returns.groupby("asset")["close"].shift(-hold) / full_returns["close"] - 1
    )

    hits = hits.merge(
        full_returns[["date", "asset", future_col]],
        on=["date", "asset"],
        how="left",
    )

    out = pd.DataFrame({
        "hypothesis_id": hypothesis.get("hypothesis_id"),
        "family": hypothesis.get("family"),
        "date": hits["date"],
        "asset": hits["asset"],
        "direction": hypothesis.get("direction", "LONG"),
        "hold_period": hold,
        "return": hits[future_col],
    })

    return out.dropna(subset=["return"])


def execute_market_hypothesis(
    hypothesis: dict[str, Any],
    market_features: pd.DataFrame,
    asset_features: pd.DataFrame,
) -> pd.DataFrame:
    """Execute market-level hypothesis."""
    if market_features.empty or asset_features.empty:
        return pd.DataFrame()

    conditions = hypothesis.get("conditions", []) or []
    mask = apply_conditions(market_features, conditions)
    hits = market_features.loc[mask].copy()

    if hits.empty:
        return pd.DataFrame()

    hold = int(hypothesis.get("hold_period", 72))
    asset_col = hypothesis.get("signal_asset_rule", "")

    if asset_col.startswith("leader_asset_") and asset_col in hits.columns:
        hits["asset"] = hits[asset_col]
    elif asset_col.startswith("asset_with_min_rank_return_"):
        window = asset_col.replace("asset_with_min_rank_return_", "")
        rank_col = f"rank_return_{window}"
        hits = select_ranked_assets(hits, asset_features, rank_col)
    else:
        return pd.DataFrame()

    hits = hits.dropna(subset=["asset"])

    joined = hits[["date", "asset"]].merge(
        asset_features[["date", "asset", "close"]],
        on=["date", "asset"],
        how="left",
    )

    future_col = f"future_return_{hold}"
    full_returns = asset_features[["date", "asset", "close"]].copy()
    full_returns = full_returns.sort_values(["asset", "date"])
    full_returns[future_col] = (
        full_returns.groupby("asset")["close"].shift(-hold) / full_returns["close"] - 1
    )

    joined = joined[["date", "asset"]].merge(
        full_returns[["date", "asset", future_col]],
        on=["date", "asset"],
        how="left",
    )

    out = pd.DataFrame({
        "hypothesis_id": hypothesis.get("hypothesis_id"),
        "family": hypothesis.get("family"),
        "date": joined["date"],
        "asset": joined["asset"],
        "direction": hypothesis.get("direction", "LONG"),
        "hold_period": hold,
        "return": joined[future_col],
    })

    return out.dropna(subset=["return"])


def select_ranked_assets(
    market_hits: pd.DataFrame,
    asset_features: pd.DataFrame,
    rank_col: str,
) -> pd.DataFrame:
    """Select asset with minimum rank at each hit timestamp."""
    if rank_col not in asset_features.columns:
        market_hits["asset"] = None
        return market_hits

    ranked = (
        asset_features.dropna(subset=[rank_col])
        .sort_values(["date", rank_col])
        .groupby("date")
        .first()
        .reset_index()[["date", "asset"]]
    )

    return market_hits.merge(ranked, on="date", how="left")
