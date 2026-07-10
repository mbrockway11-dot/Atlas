
"""Alpha Backtesting Engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.common.io import safe_read_csv

from atlas.investment.alpha.backtester.schema import (
    filter_approved_assets,
    normalize_market_frame,
)

APPROVED_UNIVERSE_PATH = (
    "output/investment_market_universe/approved_universe.csv"
)


from atlas.investment.alpha.backtester.executor import execute_hypothesis
from atlas.investment.alpha.backtester.metrics import calculate_metrics
from atlas.investment.alpha.backtester.ranking import rank_results


def non_overlapping_trades(trades: pd.DataFrame) -> pd.DataFrame:
    """Keep only non-overlapping trades per asset."""
    if trades.empty or not {"date", "asset", "hold_period"}.issubset(trades.columns):
        return trades

    rows = []
    tmp = trades.copy()
    tmp["date"] = pd.to_datetime(tmp["date"], errors="coerce")
    tmp = tmp.dropna(subset=["date"]).sort_values(["asset", "date"])

    for _, group in tmp.groupby("asset"):
        next_allowed = None
        for _, row in group.iterrows():
            date = row["date"]
            hold = int(row.get("hold_period") or 0)
            if next_allowed is None or date >= next_allowed:
                rows.append(row)
                next_allowed = date + pd.Timedelta(hours=hold)

    return pd.DataFrame(rows)


HYPOTHESES_PATH = Path("output/investment_alpha/alpha_hypotheses.json")
MARKET_FEATURES = Path("output/investment_alpha/market_features.csv")
ASSET_FEATURES = Path("output/investment_alpha/market_asset_features.csv")


def run_alpha_backtests(
    *,
    hypotheses_path: str | Path = HYPOTHESES_PATH,
    market_features_path: str | Path = MARKET_FEATURES,
    asset_features_path: str | Path = ASSET_FEATURES,
    min_trades: int = 5,
) -> dict[str, Any]:
    """Run all alpha hypothesis backtests."""
    hypotheses_payload = json.loads(Path(hypotheses_path).read_text(encoding="utf-8"))
    hypotheses = hypotheses_payload.get("hypotheses", []) or []

    market = pd.read_csv(market_features_path)
    asset = pd.read_csv(asset_features_path)

    market = normalize_market_frame(market)
    approved_universe = safe_read_csv(
        APPROVED_UNIVERSE_PATH
    )
    market = filter_approved_assets(
        market,
        approved_universe,
    )
    asset["date"] = pd.to_datetime(asset["date"], errors="coerce")

    results = []
    all_trades = []

    for hypothesis in hypotheses:
        trades = execute_hypothesis(hypothesis, market, asset)
        metrics = calculate_metrics(trades)
        non_overlap = non_overlapping_trades(trades)
        non_overlap_metrics = calculate_metrics(non_overlap)

        asset_counts = (
            trades["asset"].value_counts(dropna=False).astype(int).to_dict()
            if not trades.empty and "asset" in trades.columns
            else {}
        )
        total_asset_trades = sum(asset_counts.values())
        concentration = (
            max(asset_counts.values()) / total_asset_trades
            if total_asset_trades
            else 0.0
        )

        passed_min_trades = (non_overlap_metrics.get("trade_count") or 0) >= min_trades

        results.append(
            {
                "hypothesis_id": hypothesis.get("hypothesis_id"),
                "family": hypothesis.get("family"),
                "description": hypothesis.get("description"),
                "signal_asset_rule": hypothesis.get("signal_asset_rule"),
                "hold_period": hypothesis.get("hold_period"),
                "direction": hypothesis.get("direction"),
                "conditions": hypothesis.get("conditions", []),
                "passed_min_trades": passed_min_trades,
                "metrics": metrics,
                "non_overlapping_metrics": non_overlap_metrics,
                "asset_counts": {str(k): int(v) for k, v in asset_counts.items()},
                "asset_concentration": round(float(concentration), 6),
            }
        )

        if not trades.empty:
            all_trades.append(trades)

    ranked = rank_results(results)

    trades_df = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()

    return {
        "success": True,
        "hypothesis_count": len(hypotheses),
        "result_count": len(results),
        "min_trades": min_trades,
        "ranked_results": ranked,
        "trades": trades_df,
        "summary": (
            f"Alpha Backtesting Engine evaluated {len(results)} hypothesis/hypotheses. "
            f"Top hypothesis: {ranked[0]['hypothesis_id'] if ranked else 'n/a'}."
        ),
    }
