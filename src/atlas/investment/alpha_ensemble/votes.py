
"""Ensemble Intelligence v7 research-governed voting."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from atlas.investment.alpha_ensemble.loader import (
    approved_assets,
    metadata_by_asset,
)
from atlas.investment.alpha_ensemble.engine_votes import (
    build_research_engine_votes,
)
from atlas.investment.alpha_ensemble.governance import (
    build_engine_governance,
)


COMPONENT_WEIGHTS = {
    "research_engine_vote": 0.30,
    "feature_vote": 0.20,
    "rank_vote": 0.18,
    "backtest_vote": 0.10,
    "validation_vote": 0.08,
    "learning_vote": 0.08,
    "legacy_signal_vote": 0.06,
}


def build_asset_votes(
    inputs: dict[str, Any],
) -> list[dict]:
    assets = approved_assets(inputs)
    metadata = metadata_by_asset(inputs)

    features = latest_by_asset(
        inputs.get("market_features")
    )
    ranks = latest_by_asset(
        inputs.get("cross_sectional")
    )
    registry = latest_by_asset(
        inputs.get("strategy_registry")
    )
    learning_scores = latest_by_asset(
        inputs.get("learning_scorecard")
    )
    legacy = latest_by_asset(
        inputs.get("legacy_signals")
    )


    governance = build_engine_governance(
        inputs.get("research_decisions"),
        learning_recommendations=inputs.get(
            "engine_learning_recommendations"
        ),
        regime_suitability=inputs.get(
            "engine_regime_suitability"
        ),
        context_modifiers=inputs.get(
            "engine_context_modifiers"
        ),
    )

    research_votes = build_research_engine_votes(
        inputs.get("alpha_engine_signals"),
        governance,
    )

    global_backtest = extract_global_backtest_score(
        inputs.get("alpha_backtests", {}) or {}
    )
    global_validation = extract_global_validation_score(
        inputs.get("alpha_validation", {}) or {}
    )
    global_learning = extract_global_learning_score(
        inputs.get("learning", {}) or {}
    )

    rows = []

    for asset in assets:
        feature_row = features.get(asset, {})
        rank_row = ranks.get(asset, {})
        registry_row = registry.get(asset, {})
        learning_row = learning_scores.get(asset, {})
        legacy_row = legacy.get(asset, {})


        research_row = research_votes.get(
            asset,
            {},
        )

        research_engine_vote = (
            research_row.get(
                "research_engine_vote"
            )
            if research_row
            else None
        )

        feature_vote = build_feature_vote(feature_row)
        rank_vote = build_rank_vote(rank_row, feature_row)

        backtest_vote = build_asset_backtest_vote(
            asset,
            inputs.get("alpha_rankings"),
            fallback=global_backtest,
        )

        validation_vote = global_validation

        learning_vote = build_asset_learning_vote(
            learning_row,
            registry_row,
            fallback=global_learning,
        )

        legacy_signal_vote = build_legacy_vote(
            legacy_row
        )

        components = {
            "research_engine_vote": (
                research_engine_vote
            ),
            "feature_vote": feature_vote,
            "rank_vote": rank_vote,
            "backtest_vote": backtest_vote,
            "validation_vote": validation_vote,
            "learning_vote": learning_vote,
            "legacy_signal_vote": legacy_signal_vote,
        }

        available = {
            name: value
            for name, value in components.items()
            if value is not None
        }

        weighted_total = sum(
            available[name] * COMPONENT_WEIGHTS[name]
            for name in available
        )

        available_weight = sum(
            COMPONENT_WEIGHTS[name]
            for name in available
        )

        ensemble_score = (
            weighted_total / available_weight
            if available_weight > 0
            else 0.0
        )

        source_count = len(available)

        component_values = list(available.values())

        agreement = calculate_agreement(
            component_values
        )
        evidence_coverage = min(
            1.0,
            source_count / len(COMPONENT_WEIGHTS),
        )

        confidence = (
            evidence_coverage * 0.55
            + agreement * 0.30
            + data_quality_vote(feature_row) * 0.15
        )

        confidence = clamp(confidence)

        score = clamp(ensemble_score)

        direction = score_to_direction(score)
        action = score_to_action(
            score,
            confidence,
            registry_row,
        )

        rows.append({
            "asset": asset,
            "sector": metadata.get(asset, {}).get(
                "sector",
                "unknown",
            ),
            "tier": metadata.get(asset, {}).get(
                "tier",
                "UNKNOWN",
            ),
            **{
                name: round(value, 6)
                if value is not None
                else None
                for name, value in components.items()
            },
            "ensemble_score": round(score, 6),
            "confidence": round(confidence, 6),
            "conviction": round(
                score * confidence,
                6,
            ),
            "agreement": round(agreement, 6),
            "evidence_coverage": round(
                evidence_coverage,
                6,
            ),
            "source_count": source_count,
            "research_engine_confidence": (
                research_row.get(
                    "research_engine_confidence",
                    0.0,
                )
            ),
            "research_engine_count": (
                research_row.get(
                    "research_engine_count",
                    0,
                )
            ),
            "research_promoted_count": (
                research_row.get(
                    "research_promoted_count",
                    0,
                )
            ),
            "research_keep_count": (
                research_row.get(
                    "research_keep_count",
                    0,
                )
            ),
            "research_engine_ids": (
                research_row.get(
                    "research_engine_ids",
                    "",
                )
            ),
            "direction": direction,
            "ensemble_action": action,
            "registry_status": registry_row.get(
                "status",
                "UNREGISTERED",
            ),
            "trend_state": feature_row.get(
                "trend_state",
                "UNKNOWN",
            ),
            "volatility_state": feature_row.get(
                "volatility_state",
                "UNKNOWN",
            ),
            "return_30d": finite(
                feature_row.get("return_30d")
            ),
            "momentum_30d": finite(
                feature_row.get("momentum_30d")
            ),
            "cross_sectional_rank": finite(
                rank_row.get(
                    "final_rank",
                    rank_row.get(
                        "cross_sectional_rank",
                        0,
                    ),
                )
            ),
            "source": "ensemble_intelligence_v7",
        })

    rows.sort(
        key=lambda row: (
            -row["conviction"],
            -row["ensemble_score"],
            row["asset"],
        )
    )

    for index, row in enumerate(rows, start=1):
        row["ensemble_rank"] = index

    return rows


def build_feature_vote(row: dict) -> float | None:
    if not row:
        return None

    score = finite(
        row.get("cross_sectional_score"),
        default=0.5,
    )

    momentum_30d = finite(
        row.get("momentum_30d")
    )
    momentum_90d = finite(
        row.get("momentum_90d")
    )
    volatility = max(
        0.0,
        finite(row.get("volatility_30d")),
    )
    drawdown = finite(
        row.get("drawdown_from_90d_high")
    )

    momentum_score = clamp(
        0.5
        + momentum_30d * 1.5
        + momentum_90d * 0.5
    )

    volatility_penalty = clamp(
        volatility / 2.5
    )

    drawdown_penalty = clamp(
        abs(min(drawdown, 0.0)) * 1.25
    )

    trend = str(
        row.get("trend_state", "")
    ).upper()

    trend_bonus = {
        "UPTREND": 0.10,
        "NEUTRAL": 0.0,
        "DOWNTREND": -0.10,
    }.get(trend, 0.0)

    result = (
        score * 0.35
        + momentum_score * 0.45
        + (1.0 - volatility_penalty) * 0.10
        + (1.0 - drawdown_penalty) * 0.10
        + trend_bonus
    )

    return clamp(result)


def build_rank_vote(
    rank_row: dict,
    feature_row: dict,
) -> float | None:
    if rank_row:
        score = first_number(
            rank_row,
            [
                "final_alpha_score",
                "cross_sectional_score",
                "cross_sectional_percentile",
            ],
        )

        if score is not None:
            return normalize_observed_score(score)

    if feature_row:
        score = first_number(
            feature_row,
            [
                "cross_sectional_score",
                "cross_sectional_percentile",
            ],
        )

        if score is not None:
            return clamp(score)

    return None


def build_asset_backtest_vote(
    asset: str,
    rankings: pd.DataFrame | None,
    *,
    fallback: float,
) -> float:
    if (
        rankings is None
        or rankings.empty
    ):
        return fallback

    frame = rankings.copy()

    asset_columns = [
        column
        for column in [
            "asset",
            "leader_asset",
            "trade_asset",
        ]
        if column in frame.columns
    ]

    if asset_columns:
        mask = pd.Series(
            False,
            index=frame.index,
        )

        for column in asset_columns:
            mask = (
                mask
                | frame[column].astype(str).eq(asset)
            )

        asset_frame = frame[mask]
    else:
        asset_frame = pd.DataFrame()

    if asset_frame.empty:
        return fallback

    row = asset_frame.iloc[0]

    score = first_number(
        row,
        [
            "score",
            "non_overlapping_profit_factor",
            "profit_factor",
            "win_rate",
        ],
    )

    if score is None:
        return fallback

    return normalize_observed_score(score)


def build_asset_learning_vote(
    learning_row: dict,
    registry_row: dict,
    *,
    fallback: float,
) -> float:
    values = []

    for row, candidates in [
        (
            learning_row,
            [
                "asset_confidence",
                "confidence",
                "score",
            ],
        ),
        (
            registry_row,
            [
                "asset_confidence",
                "learning_confidence",
                "weight_multiplier",
            ],
        ),
    ]:
        value = first_number(row, candidates)

        if value is not None:
            values.append(
                normalize_observed_score(value)
            )

    if not values:
        return fallback

    return clamp(sum(values) / len(values))


def build_legacy_vote(row: dict) -> float | None:
    if not row:
        return None

    raw = first_number(
        row,
        [
            "raw_score",
            "ensemble_score",
            "signal_score",
            "confidence",
        ],
    )

    if raw is None:
        return None

    direction = str(
        row.get(
            "direction",
            row.get(
                "signal_direction",
                "LONG",
            ),
        )
    ).upper()

    score = normalize_observed_score(raw)

    if direction in {
        "SHORT",
        "SELL",
        "BEARISH",
        "DOWN",
    }:
        return clamp(1.0 - score)

    return score


def extract_global_backtest_score(
    report: dict,
) -> float:
    rankings = (
        report.get("rankings")
        or report.get("results")
        or []
    )

    if rankings:
        row = rankings[0]

        value = first_number(
            row,
            [
                "score",
                "profit_factor",
                "win_rate",
            ],
        )

        if value is not None:
            return normalize_observed_score(value)

    return 0.50


def extract_global_validation_score(
    report: dict,
) -> float:
    for container in [
        report,
        report.get("summary", {}) or {},
        report.get("validation_summary", {}) or {},
    ]:
        value = first_number(
            container,
            [
                "validation_score",
                "confidence",
                "pass_rate",
                "robustness_score",
            ],
        )

        if value is not None:
            return normalize_observed_score(value)

    success = report.get("success")

    if success is True:
        return 0.65
    if success is False:
        return 0.35

    return 0.50


def extract_global_learning_score(
    report: dict,
) -> float:
    for container in [
        report,
        report.get("summary", {}) or {},
        report.get("regime", {}) or {},
    ]:
        value = first_number(
            container,
            [
                "overall_confidence",
                "confidence",
                "learning_confidence",
                "score",
            ],
        )

        if value is not None:
            return normalize_observed_score(value)

    return 0.50


def data_quality_vote(row: dict) -> float:
    if not row:
        return 0.0

    required = [
        "close",
        "return_30d",
        "momentum_30d",
        "volatility_30d",
        "cross_sectional_score",
    ]

    present = sum(
        1
        for column in required
        if column in row
        and row.get(column) is not None
        and not pd.isna(row.get(column))
    )

    return present / len(required)


def calculate_agreement(
    values: list[float],
) -> float:
    if not values:
        return 0.0

    if len(values) == 1:
        return 0.5

    array = np.asarray(values, dtype=float)
    dispersion = float(
        np.std(array, ddof=0)
    )

    return clamp(1.0 - dispersion * 2.0)


def score_to_direction(score: float) -> str:
    if score >= 0.60:
        return "LONG"
    if score <= 0.40:
        return "SHORT"
    return "NEUTRAL"


def score_to_action(
    score: float,
    confidence: float,
    registry_row: dict,
) -> str:
    registry_status = str(
        registry_row.get("status", "")
    ).upper()

    if registry_status in {
        "RETIRED",
        "BLOCKED",
        "REJECTED",
    }:
        return "AVOID"

    conviction = score * confidence

    if score >= 0.68 and conviction >= 0.48:
        return "PROMOTE_LONG"

    if score >= 0.56:
        return "MAINTAIN"

    if score >= 0.46:
        return "WATCH"

    if score >= 0.36:
        return "ROTATING_OUT"

    return "AVOID"


def latest_by_asset(
    frame: pd.DataFrame | None,
) -> dict[str, dict]:
    if (
        frame is None
        or frame.empty
        or "asset" not in frame.columns
    ):
        return {}

    working = frame.copy()

    if "timestamp" in working.columns:
        working["timestamp"] = pd.to_datetime(
            working["timestamp"],
            errors="coerce",
            utc=True,
        )
        working = working.sort_values(
            "timestamp",
            kind="stable",
        )
    elif "date" in working.columns:
        working["date"] = pd.to_datetime(
            working["date"],
            errors="coerce",
            utc=True,
        )
        working = working.sort_values(
            "date",
            kind="stable",
        )

    working = working.drop_duplicates(
        subset=["asset"],
        keep="last",
    )

    return {
        str(row.get("asset")): row.to_dict()
        for _, row in working.iterrows()
    }


def first_number(
    row,
    columns: list[str],
) -> float | None:
    if row is None:
        return None

    for column in columns:
        try:
            if column not in row:
                continue
            value = row.get(column)
        except AttributeError:
            continue

        if value is None or pd.isna(value):
            continue

        try:
            result = float(value)
        except (TypeError, ValueError):
            continue

        if math.isfinite(result):
            return result

    return None


def normalize_observed_score(
    value: float,
) -> float:
    value = finite(value)

    if 0.0 <= value <= 1.0:
        return value

    if value < 0.0:
        return clamp(0.5 + value / 4.0)

    return clamp(value / (value + 1.0))


def finite(
    value,
    *,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default

    return result if math.isfinite(result) else default


def clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))






