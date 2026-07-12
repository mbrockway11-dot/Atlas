"""Adaptive Research Prioritizer v1 configuration."""

from __future__ import annotations

from pathlib import Path


VERSION = "adaptive_research_prioritizer_v1"
SCHEMA_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_adaptive_research_prioritizer"
)

PRIORITY_QUEUE_CSV = (
    OUTPUT_DIR
    / "research_priority_queue.csv"
)

CANDIDATE_SCORES_CSV = (
    OUTPUT_DIR
    / "research_candidate_scores.csv"
)

SCORE_COMPONENTS_CSV = (
    OUTPUT_DIR
    / "research_score_components.csv"
)

DUPLICATION_FLAGS_CSV = (
    OUTPUT_DIR
    / "research_duplication_flags.csv"
)

COVERAGE_GAPS_CSV = (
    OUTPUT_DIR
    / "research_coverage_gaps.csv"
)

EXPLANATIONS_CSV = (
    OUTPUT_DIR
    / "research_priority_explanations.csv"
)

PRIORITY_HISTORY_CSV = (
    OUTPUT_DIR
    / "research_priority_history.csv"
)

STATE_JSON = (
    OUTPUT_DIR
    / "research_prioritizer_state.json"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "research_prioritizer_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "research_prioritizer_report.md"
)

SOURCE = VERSION

SCORE_WEIGHTS = {
    "source_priority": 0.16,
    "failure_recurrence": 0.15,
    "coverage_gap": 0.13,
    "graph_importance": 0.10,
    "validation_potential": 0.12,
    "regime_relevance": 0.12,
    "novelty": 0.10,
    "implementation_readiness": 0.07,
    "evidence_quality": 0.05,
}

PRIORITY_THRESHOLDS = {
    "CRITICAL": 0.80,
    "HIGH": 0.65,
    "MEDIUM": 0.45,
    "LOW": 0.00,
}

RECOMMENDATION_THRESHOLDS = {
    "RESEARCH_NOW": 0.70,
    "QUEUE": 0.50,
    "MONITOR": 0.30,
    "DEFER": 0.00,
}
