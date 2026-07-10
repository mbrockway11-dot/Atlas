
"""Alpha backtest ranking."""

from __future__ import annotations

from typing import Any


MIN_NON_OVERLAP_TRADES = 30
MAX_ASSET_CONCENTRATION = 0.75


def rank_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank backtest results using diversified non-overlapping metrics."""

    def score(row: dict[str, Any]) -> float:
        m = row.get("non_overlapping_metrics", {}) or row.get("metrics", {}) or {}

        trade_count = m.get("trade_count") or 0
        avg_return = m.get("avg_return") or 0
        win_rate = m.get("win_rate") or 0
        profit_factor = m.get("profit_factor") or 0
        max_dd = abs(m.get("max_drawdown") or 0)
        max_return = m.get("max_return") or 0
        concentration = row.get("asset_concentration") or 0

        if trade_count < MIN_NON_OVERLAP_TRADES:
            return -999.0

        if concentration > MAX_ASSET_CONCENTRATION:
            return -500.0 + (MAX_ASSET_CONCENTRATION - concentration)

        if avg_return <= 0:
            return -250.0 + avg_return

        sample_score = min(trade_count / 100, 1.0)
        pf_score = min(profit_factor or 0, 5) / 5
        dd_penalty = max_dd * 2
        concentration_penalty = concentration * 0.75
        outlier_penalty = max(0.0, max_return - 3.0) * 0.35

        return round(
            sample_score
            + avg_return * 10
            + win_rate
            + pf_score
            - dd_penalty
            - concentration_penalty
            - outlier_penalty,
            6,
        )

    ranked = []
    for row in results:
        enriched = dict(row)
        enriched["ranking_version"] = "diversified_v1_2"
        enriched["ranking_constraints"] = {
            "min_non_overlap_trades": MIN_NON_OVERLAP_TRADES,
            "max_asset_concentration": MAX_ASSET_CONCENTRATION,
            "requires_positive_non_overlap_avg": True,
        }
        enriched["alpha_score"] = score(row)
        enriched["passed_diversified_ranking"] = enriched["alpha_score"] > -100
        ranked.append(enriched)

    return sorted(ranked, key=lambda item: item.get("alpha_score", -999), reverse=True)
