
"""Alpha ensemble confidence."""

from __future__ import annotations

from typing import Any

import pandas as pd


def calculate_ensemble_confidence(signal_row: dict[str, Any] | pd.Series) -> dict[str, Any]:
    """Calculate confidence for one ensemble signal."""
    if hasattr(signal_row, "to_dict"):
        row = signal_row.to_dict()
    else:
        row = dict(signal_row)

    total_weight = float(row.get("total_weight") or 0.0)
    net_score = float(row.get("net_long_score") or 0.0)
    strategy_count = int(row.get("strategy_count") or 0)

    consensus = abs(net_score) / total_weight if total_weight else 0.0
    breadth = min(strategy_count / 5, 1.0)

    confidence = consensus * 0.70 + breadth * 0.30

    return {
        "ensemble_confidence": round(float(confidence), 6),
        "consensus_score": round(float(consensus), 6),
        "breadth_score": round(float(breadth), 6),
        "confidence_label": label(confidence),
    }


def label(score: float) -> str:
    if score >= 0.85:
        return "strong_ensemble_signal"
    if score >= 0.70:
        return "moderate_ensemble_signal"
    if score >= 0.55:
        return "weak_ensemble_signal"
    return "noisy_ensemble_signal"
