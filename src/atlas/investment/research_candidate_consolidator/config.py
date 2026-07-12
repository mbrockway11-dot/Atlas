"""Atlas Research Candidate Consolidator v1 configuration."""

from __future__ import annotations

from pathlib import Path


VERSION = "atlas_research_candidate_consolidator_v1"
SCHEMA_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_research_candidate_consolidator"
)

PROGRAMS_CSV = (
    OUTPUT_DIR
    / "consolidated_research_programs.csv"
)

MEMBERS_CSV = (
    OUTPUT_DIR
    / "research_program_members.csv"
)

DIMENSIONS_CSV = (
    OUTPUT_DIR
    / "research_program_dimensions.csv"
)

CONFLICTS_CSV = (
    OUTPUT_DIR
    / "research_program_conflicts.csv"
)

PROGRAM_SCORES_CSV = (
    OUTPUT_DIR
    / "research_program_scores.csv"
)

UNCONSOLIDATED_CSV = (
    OUTPUT_DIR
    / "unconsolidated_candidates.csv"
)

AUDIT_CSV = (
    OUTPUT_DIR
    / "consolidation_audit.csv"
)

HISTORY_CSV = (
    OUTPUT_DIR
    / "consolidation_history.csv"
)

STATE_JSON = (
    OUTPUT_DIR
    / "research_candidate_consolidator_state.json"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "research_candidate_consolidator_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "research_candidate_consolidator_report.md"
)

SOURCE = VERSION

MIN_CLUSTER_SIZE = 2
MIN_PAIR_SIMILARITY = 0.42
MIN_CLUSTER_CONFIDENCE = 0.45

FEATURE_FAMILIES = {
    "volatility": {
        "atr",
        "volatility",
        "vol",
        "range",
        "compression",
        "expansion",
    },
    "trend": {
        "trend",
        "sma",
        "ema",
        "moving_average",
        "distance_sma",
        "distance_ema",
    },
    "liquidity": {
        "liquidity",
        "volume",
        "volume_ratio",
        "turnover",
        "spread",
    },
    "momentum": {
        "momentum",
        "rsi",
        "roc",
        "acceleration",
    },
    "returns": {
        "return",
        "drawdown",
        "recovery",
        "performance",
    },
    "regime": {
        "regime",
        "risk_on",
        "risk_off",
        "transition",
        "dispersion",
    },
    "direction": {
        "direction",
        "long",
        "short",
    },
    "structure": {
        "breakout",
        "reversal",
        "continuation",
        "cross_sectional",
        "relative_strength",
    },
}

CONDITION_VALUES = {
    "LOW",
    "MID",
    "HIGH",
    "NORMAL",
    "CONTRACTING",
    "EXPANDING",
    "UPTREND",
    "DOWNTREND",
    "NEUTRAL",
    "TRANSITION",
    "LONG",
    "SHORT",
    "TRUE",
    "FALSE",
}
