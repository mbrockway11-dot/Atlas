
"""Alpha ensemble signal builder."""

from __future__ import annotations

from typing import Any

import pandas as pd

from atlas.investment.alpha.ensemble.confidence import calculate_ensemble_confidence
from atlas.investment.alpha.ensemble.voting import aggregate_votes, build_strategy_votes
from atlas.investment.alpha.ensemble.weighting import build_strategy_weights


def build_ensemble_signals(
    strategies: list[dict[str, Any]],
    trades: pd.DataFrame,
) -> dict[str, Any]:
    """Build historical ensemble signals from promoted strategies."""
    weights = build_strategy_weights(strategies)
    votes = build_strategy_votes(trades, weights)
    signals = aggregate_votes(votes)

    if not signals.empty:
        confidence_rows = [calculate_ensemble_confidence(row) for _, row in signals.iterrows()]
        conf_df = pd.DataFrame(confidence_rows)
        signals = pd.concat([signals.reset_index(drop=True), conf_df.reset_index(drop=True)], axis=1)

    latest = {}
    if not signals.empty:
        latest_row = signals.sort_values("date").iloc[-1].to_dict()
        latest = latest_row

    return {
        "success": True,
        "weights": weights,
        "votes": votes,
        "signals": signals,
        "latest_signal": latest,
        "summary": (
            f"Alpha Ensemble built {len(signals)} historical signal row(s) "
            f"from {len(strategies)} promoted strategy/strategies."
        ),
    }
