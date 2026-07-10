
"""Alpha Ensemble v4 scoring."""

from __future__ import annotations

import pandas as pd


SOURCE_WEIGHTS = {
    "strategy_registry_v3": 0.35,
    "alpha_backtests": 0.25,
    "sigil_v32_adapter": 0.20,
    "market_direction": 0.15,
    "fallback": 0.05,
}


def score_ensemble(signals: list[dict], learning: dict, performance: dict) -> list[dict]:
    if not signals:
        return []

    df = pd.DataFrame(signals)
    rows = []

    regime_mult = regime_multiplier(learning)
    perf_mult = performance_multiplier(performance)

    for asset, group in df.groupby("asset"):
        weighted_sum = 0.0
        weight_total = 0.0
        source_count = 0

        for _, row in group.iterrows():
            source = str(row.get("signal_source"))
            source_weight = SOURCE_WEIGHTS.get(source, 0.05)
            confidence = float(row.get("confidence") or row.get("raw_score") or 0.5)

            direction = str(row.get("direction") or "LONG").upper()
            signed_score = confidence

            if direction in {"SHORT", "SELL", "REDUCE"}:
                signed_score = 1.0 - confidence

            weighted_sum += signed_score * source_weight
            weight_total += source_weight
            source_count += 1

        conviction = weighted_sum / weight_total if weight_total else 0.0
        conviction = max(0.0, min(1.0, conviction * regime_mult * perf_mult))

        rows.append({
            "asset": asset,
            "ensemble_score": round(conviction, 6),
            "conviction": round(conviction, 6),
            "source_count": source_count,
            "regime_multiplier": round(regime_mult, 6),
            "performance_multiplier": round(perf_mult, 6),
            "ensemble_action": action_from_score(conviction),
            "source": "alpha_ensemble_v4",
        })

    return sorted(rows, key=lambda r: r["ensemble_score"], reverse=True)


def action_from_score(score: float) -> str:
    if score >= 0.62:
        return "PROMOTE_LONG"
    if score <= 0.40:
        return "REDUCE_OR_AVOID"
    return "MAINTAIN"


def regime_multiplier(learning: dict) -> float:
    regime = (learning.get("learning_regime", {}) or {}).get("learning_regime", "unknown")
    confidence = float(learning.get("learning_confidence") or 0.0)

    if regime == "improving":
        return min(1.15, 1.0 + confidence * 0.15)
    if regime == "deteriorating":
        return max(0.65, 1.0 - confidence * 0.35)
    if regime == "insufficient_history":
        return 0.90
    return 1.0


def performance_multiplier(performance: dict) -> float:
    metrics = performance.get("equity_metrics", {}) or {}
    sharpe = float(metrics.get("sharpe") or 0.0)
    max_dd = float(metrics.get("max_drawdown") or 0.0)

    mult = 1.0

    if sharpe > 1.0:
        mult += 0.05
    elif sharpe < -0.5:
        mult -= 0.10

    if max_dd <= -0.10:
        mult -= 0.15

    return max(0.60, min(1.15, mult))
