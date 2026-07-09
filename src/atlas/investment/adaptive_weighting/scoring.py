
"""Adaptive family scoring."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd

from atlas.investment.adaptive_weighting.family_map import strategy_family_from_id


DEFAULT_FAMILY_WEIGHTS = {
    "portfolio_allocation": 0.25,
    "cross_sectional_ranking": 0.25,
    "intraday_execution": 0.20,
    "momentum": 0.10,
    "breadth": 0.10,
    "leadership": 0.05,
    "topology": 0.05,
}


def score_from_rankings(rankings: pd.DataFrame) -> dict[str, float]:
    """Build family scores from alpha ranking performance."""
    if rankings.empty:
        return {}

    df = rankings.copy()

    if "hypothesis_id" not in df.columns:
        return {}

    if "alpha_score" not in df.columns:
        df["alpha_score"] = 0.0

    df["alpha_score"] = pd.to_numeric(df["alpha_score"], errors="coerce").fillna(0.0)
    df["family"] = df["hypothesis_id"].apply(strategy_family_from_id)

    scores = {}

    for family, group in df.groupby("family"):
        top = group.sort_values("alpha_score", ascending=False).head(5)
        score = max(float(top["alpha_score"].mean()), 0.0)
        scores[family] = score

    return normalize_scores(scores)


def score_from_validated(validated: list[dict[str, Any]]) -> dict[str, float]:
    """Build family scores from promoted strategy confidence."""
    if not validated:
        return {}

    raw = defaultdict(list)

    for item in validated:
        sid = item.get("hypothesis_id")
        family = strategy_family_from_id(sid)

        confidence = (
            item.get("confidence", {}) or {}
        ).get("alpha_confidence", 0.0)

        try:
            raw[family].append(float(confidence))
        except Exception:
            pass

    scores = {
        family: sum(values) / len(values)
        for family, values in raw.items()
        if values
    }

    return normalize_scores(scores)


def score_from_walkforward(walkforward: dict[str, Any]) -> dict[str, float]:
    """Build broad confidence score from walk-forward stability."""
    if not walkforward:
        return {}

    agg = walkforward.get("aggregate_test", {}) or {}

    stability = float(walkforward.get("stability_score") or 0.0)
    pf = float(agg.get("profit_factor") or 0.0)
    dd = abs(float(agg.get("max_drawdown") or 0.0))

    quality = stability

    if pf > 1:
        quality += min((pf - 1) / 5, 0.40)

    if dd > 0:
        quality -= min(dd, 0.50) * 0.25

    quality = max(0.0, min(quality, 1.0))

    # Walk-forward validates the alpha stack broadly.
    return {
        "portfolio_allocation": quality,
        "cross_sectional_ranking": quality,
        "momentum": quality * 0.75,
        "breadth": quality * 0.75,
        "leadership": quality * 0.75,
        "topology": quality * 0.75,
    }


def combine_family_scores(*score_maps: dict[str, float]) -> dict[str, float]:
    combined = defaultdict(list)

    for score_map in score_maps:
        for family, score in score_map.items():
            combined[family].append(float(score))

    raw = {}

    for family in DEFAULT_FAMILY_WEIGHTS:
        values = combined.get(family, [])
        if values:
            raw[family] = sum(values) / len(values)
        else:
            raw[family] = DEFAULT_FAMILY_WEIGHTS[family]

    return normalize_scores(raw)


def normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    cleaned = {k: max(float(v), 0.0) for k, v in scores.items()}
    total = sum(cleaned.values())

    if total <= 0:
        return {}

    return {
        k: round(v / total, 6)
        for k, v in cleaned.items()
    }
