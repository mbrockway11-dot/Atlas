"""Alpha Ensemble v6.1 loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from atlas.common.io import (
    safe_read_csv,
    safe_read_json,
)


APPROVED_UNIVERSE = Path(
    "output/investment_market_universe/approved_universe.csv"
)

MARKET_FEATURES = Path(
    "output/investment_alpha/market_features.csv"
)

CROSS_SECTIONAL = Path(
    "output/investment_alpha/cross_sectional_alpha_latest.csv"
)

CROSS_SECTIONAL_FALLBACK = Path(
    "output/investment_alpha/cross_sectional_alpha_rankings.csv"
)

ALPHA_BACKTESTS_JSON = Path(
    "output/investment_alpha/alpha_backtests.json"
)

ALPHA_RANKINGS = Path(
    "output/investment_alpha/alpha_rankings.csv"
)

ALPHA_VALIDATION = Path(
    "output/investment_alpha/alpha_validation_report.json"
)

STRATEGY_REGISTRY = Path(
    "output/investment_strategy_registry/strategy_registry.csv"
)

LEARNING_REPORT = Path(
    "output/investment_learning/learning_report.json"
)

LEARNING_SCORECARD = Path(
    "output/investment_learning/strategy_scorecard.csv"
)

PERFORMANCE_REPORT = Path(
    "output/investment_performance/performance_report.json"
)

MARKET_DIRECTION = Path(
    "output/investment_market_direction/market_direction_report.json"
)

LEGACY_SIGNALS = Path(
    "output/investment_alpha_ensemble/alpha_ensemble_signals.csv"
)

ALPHA_ENGINE_LATEST = Path(
    "output/investment_alpha_engines/alpha_engine_latest.csv"
)

RESEARCH_DECISIONS = Path(
    "output/investment_alpha_research_lab/"
    "alpha_research_promotion_decisions.csv"
)

ENGINE_LEARNING_RECOMMENDATIONS = Path(
    "output/investment_learning/"
    "engine_learning_recommendations.csv"
)

ENGINE_REGIME_SUITABILITY = Path(
    "output/investment_regime_intelligence/"
    "engine_regime_suitability.csv"
)

REGIME_INTELLIGENCE_REPORT = Path(
    "output/investment_regime_intelligence/"
    "regime_intelligence_report.json"
)

UNIVERSE_REPORT = Path(
    "output/investment_market_universe/market_universe_report.json"
)


def load_alpha_ensemble_inputs() -> dict[str, Any]:
    """Load Alpha Ensemble v6.1 inputs without failing on absent artifacts."""
    cross_sectional = safe_read_csv(
        CROSS_SECTIONAL
    )

    if cross_sectional.empty:
        cross_sectional = safe_read_csv(
            CROSS_SECTIONAL_FALLBACK
        )

    return {
        "approved_universe": safe_read_csv(
            APPROVED_UNIVERSE
        ),
        "universe_report": safe_read_json(
            UNIVERSE_REPORT
        ),
        "market_features": safe_read_csv(
            MARKET_FEATURES
        ),
        "cross_sectional": cross_sectional,
        "alpha_backtests": safe_read_json(
            ALPHA_BACKTESTS_JSON
        ),
        "alpha_rankings": safe_read_csv(
            ALPHA_RANKINGS
        ),
        "alpha_validation": safe_read_json(
            ALPHA_VALIDATION
        ),
        "strategy_registry": safe_read_csv(
            STRATEGY_REGISTRY
        ),
        "learning": safe_read_json(
            LEARNING_REPORT
        ),
        "learning_scorecard": safe_read_csv(
            LEARNING_SCORECARD
        ),
        "performance": safe_read_json(
            PERFORMANCE_REPORT
        ),
        "market_direction": safe_read_json(
            MARKET_DIRECTION
        ),
        "legacy_signals": safe_read_csv(
            LEGACY_SIGNALS
        ),
        "alpha_engine_signals": safe_read_csv(
            ALPHA_ENGINE_LATEST
        ),
        "research_decisions": safe_read_csv(
            RESEARCH_DECISIONS
        ),
        "engine_learning_recommendations": safe_read_csv(
            ENGINE_LEARNING_RECOMMENDATIONS
        ),
        "engine_regime_suitability": safe_read_csv(
            ENGINE_REGIME_SUITABILITY
        ),
        "regime_intelligence": safe_read_json(
            REGIME_INTELLIGENCE_REPORT
        ),
    }


def approved_assets(
    inputs: dict[str, Any],
) -> list[str]:
    """Return deterministic approved-universe assets."""
    frame = inputs.get(
        "approved_universe"
    )

    if (
        frame is not None
        and not frame.empty
        and "asset" in frame.columns
    ):
        return (
            frame["asset"]
            .dropna()
            .astype(str)
            .drop_duplicates()
            .tolist()
        )

    report = (
        inputs.get(
            "universe_report",
            {},
        )
        or {}
    )

    return [
        str(asset)
        for asset in report.get(
            "approved_assets",
            [],
        )
    ]


def metadata_by_asset(
    inputs: dict[str, Any],
) -> dict[str, dict]:
    """Index approved-universe metadata by asset."""
    frame = inputs.get(
        "approved_universe"
    )

    if (
        frame is None
        or frame.empty
        or "asset" not in frame.columns
    ):
        return {}

    return {
        str(
            row.get("asset")
        ): row.to_dict()
        for _, row in frame.iterrows()
    }


