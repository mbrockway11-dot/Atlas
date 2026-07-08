
"""Normalize strategy outputs into registry signals."""

from __future__ import annotations

import pandas as pd

from atlas.investment.strategy_registry.schema import RegisteredStrategySignal


def as_float(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass

    try:
        return float(value)
    except Exception:
        return default


def normalize_sigil_v32(df: pd.DataFrame) -> list[RegisteredStrategySignal]:
    signals: list[RegisteredStrategySignal] = []

    if df.empty:
        return signals

    for _, row in df.iterrows():
        signals.append(
            RegisteredStrategySignal(
                source="sigil_v32",
                strategy_id=str(row.get("engine")),
                strategy_family="intraday_execution",
                asset=row.get("asset"),
                timestamp=str(row.get("timestamp")) if row.get("timestamp") is not None else None,
                action=row.get("action"),
                direction=row.get("direction"),
                confidence=1.0 if row.get("action") not in {None, "NO_ACTION"} else 0.0,
                target_exposure=as_float(row.get("target_exposure"), 0.0),
                rank=None,
                notes=row.get("notes"),
            )
        )

    return signals


def normalize_alpha_portfolio(df: pd.DataFrame) -> list[RegisteredStrategySignal]:
    signals: list[RegisteredStrategySignal] = []

    if df.empty:
        return signals

    for _, row in df.iterrows():
        asset = row.get("asset")
        if asset == "CASH":
            continue

        weight = as_float(row.get("target_weight"), 0.0)

        signals.append(
            RegisteredStrategySignal(
                source="atlas_alpha",
                strategy_id="alpha_portfolio_construction",
                strategy_family="portfolio_allocation",
                asset=asset,
                timestamp=None,
                action="ALLOCATE" if weight > 0 else "NO_ACTION",
                direction="LONG" if weight > 0 else "FLAT",
                confidence=as_float(row.get("ensemble_confidence"), 0.0),
                target_exposure=weight,
                rank=as_float(row.get("rank"), 0.0),
                notes=row.get("reason"),
            )
        )

    return signals


def normalize_cross_sectional_ranker(df: pd.DataFrame) -> list[RegisteredStrategySignal]:
    signals: list[RegisteredStrategySignal] = []

    if df.empty:
        return signals

    for _, row in df.iterrows():
        rank = as_float(row.get("final_rank"), 999.0)
        score = as_float(row.get("final_alpha_score"), 0.0)

        if rank <= 3 and score > 0:
            action = "WATCH"
            direction = "LONG"
        else:
            action = "NO_ACTION"
            direction = "FLAT"

        signals.append(
            RegisteredStrategySignal(
                source="atlas_alpha",
                strategy_id="cross_sectional_alpha_ranker",
                strategy_family="cross_sectional_ranking",
                asset=row.get("asset"),
                timestamp=str(row.get("date")) if row.get("date") is not None else None,
                action=action,
                direction=direction,
                confidence=min(max(score, 0.0), 1.0),
                target_exposure=0.0,
                rank=rank,
                notes=row.get("final_rank_label"),
            )
        )

    return signals
