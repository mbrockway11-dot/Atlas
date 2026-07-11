"""Meta Research Engine v1 configuration."""

from __future__ import annotations

from pathlib import Path


OUTPUT_DIR = Path(
    "output/investment_meta_research"
)

ENGINE_DIAGNOSTICS_CSV = (
    OUTPUT_DIR
    / "engine_diagnostics.csv"
)

FEATURE_INTERACTIONS_CSV = (
    OUTPUT_DIR
    / "feature_interactions.csv"
)

FAILURE_MODES_CSV = (
    OUTPUT_DIR
    / "engine_failure_modes.csv"
)

FAMILY_GAPS_CSV = (
    OUTPUT_DIR
    / "engine_family_gaps.csv"
)

RESEARCH_PRIORITIES_CSV = (
    OUTPUT_DIR
    / "research_priorities.csv"
)

HYPOTHESIS_LIBRARY_CSV = (
    OUTPUT_DIR
    / "hypothesis_library.csv"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "meta_research_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "meta_research_report.md"
)

VERSION = "meta_research_engine_v1"
SCHEMA_VERSION = "1.0.0"

MIN_ENGINE_TRADES = 20
MIN_SEGMENT_TRADES = 12
MIN_FEATURE_COVERAGE = 0.50

STRONG_PROFIT_FACTOR = 1.20
WEAK_PROFIT_FACTOR = 0.95

POSITIVE_MEAN_THRESHOLD = 0.0025
NEGATIVE_MEAN_THRESHOLD = -0.0025

MIN_POSITIVE_LIFT = 0.005
MIN_NEGATIVE_LIFT = 0.005

MAX_HYPOTHESES = 50

FEATURE_COLUMNS = [
    "return_1d",
    "return_7d",
    "return_14d",
    "return_30d",
    "return_90d",
    "momentum_14d",
    "momentum_30d",
    "momentum_90d",
    "volatility_7d",
    "volatility_30d",
    "atr_pct_14d",
    "distance_sma_7d",
    "distance_sma_14d",
    "distance_sma_30d",
    "drawdown_from_90d_high",
    "volume_ratio_30d",
    "cross_sectional_score",
    "cross_sectional_percentile",
]

CATEGORICAL_COLUMNS = [
    "trend_state",
    "volatility_state",
    "liquidity_state",
    "regime",
    "direction",
]

EXPECTED_ENGINE_FAMILIES = [
    "trend",
    "momentum",
    "mean_reversion",
    "drawdown_recovery",
    "volatility_expansion",
    "volatility_compression",
    "market_breadth",
    "breakout",
    "liquidity",
    "correlation_dispersion",
    "relative_value",
    "defensive_risk_off",
]
