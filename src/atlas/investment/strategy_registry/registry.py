
"""Strategy Registry v3 state builder."""

from __future__ import annotations

from datetime import datetime, UTC
import pandas as pd

from atlas.investment.strategy_registry.lifecycle import lifecycle_status, next_weight_multiplier


def build_registry_state(inputs: dict) -> dict:
    learning = inputs.get("learning", {}) or {}
    scorecard = inputs.get("scorecard")
    performance = inputs.get("performance", {}) or {}
    prior = inputs.get("prior_state", {}) or {}

    regime = (learning.get("learning_regime", {}) or {}).get("learning_regime", "unknown")
    learning_confidence = float(learning.get("learning_confidence") or 0.0)

    rows = []

    if scorecard is not None and not scorecard.empty:
        for _, row in scorecard.iterrows():
            asset = str(row.get("asset"))
            conf = float(row.get("asset_confidence") or 0.0)
            recommendation = str(row.get("recommendation") or "maintain")

            status = lifecycle_status(recommendation, conf, regime)

            prior_entry = find_prior_asset(prior, asset)

            rows.append({
                "strategy_id": f"asset::{asset}",
                "strategy_type": "asset_allocation",
                "asset": asset,
                "status": status,
                "recommendation": recommendation,
                "asset_confidence": round(conf, 6),
                "learning_confidence": round(learning_confidence, 6),
                "learning_regime": regime,
                "weight_multiplier": next_weight_multiplier(status),
                "age_runs": int(prior_entry.get("age_runs", 0)) + 1,
                "promote_count": int(prior_entry.get("promote_count", 0)) + (1 if status == "PROMOTE" else 0),
                "reduce_count": int(prior_entry.get("reduce_count", 0)) + (1 if status == "REDUCE" else 0),
                "review_retire_count": int(prior_entry.get("review_retire_count", 0)) + (1 if status == "REVIEW_RETIRE" else 0),
                "updated_at": datetime.now(UTC).isoformat(),
            })

    equity_metrics = performance.get("equity_metrics", {}) or {}

    return {
        "version": "strategy_registry_v3",
        "source": "learning_engine_v3",
        "updated_at": datetime.now(UTC).isoformat(),
        "learning_regime": regime,
        "learning_confidence": round(learning_confidence, 6),
        "performance_snapshot": {
            "pnl_pct": equity_metrics.get("pnl_pct", 0.0),
            "sharpe": equity_metrics.get("sharpe", 0.0),
            "max_drawdown": equity_metrics.get("max_drawdown", 0.0),
        },
        "strategies": rows,
        "counts": count_statuses(rows),
    }


def find_prior_asset(prior: dict, asset: str) -> dict:
    for row in prior.get("strategies", []) or []:
        if str(row.get("asset")) == str(asset):
            return row
    return {}


def count_statuses(rows: list[dict]) -> dict:
    counts = {}

    for row in rows:
        status = row.get("status")
        counts[status] = counts.get(status, 0) + 1

    return counts
