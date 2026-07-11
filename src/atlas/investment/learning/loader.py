"""Learning Engine v3.1 loaders."""

from __future__ import annotations

from pathlib import Path

from atlas.common.io import (
    safe_read_csv,
    safe_read_json,
)


PERFORMANCE_REPORT = Path(
    "output/investment_performance/performance_report.json"
)

EQUITY_CURVE = Path(
    "output/investment_mark_to_market/equity_curve.csv"
)

BROKER_FILLS = Path(
    "output/investment_paper_broker/paper_broker_fills.csv"
)

ATTRIBUTION = Path(
    "output/investment_performance/performance_attribution.csv"
)

RISK_REPORT = Path(
    "output/investment_risk/risk_engine_report.json"
)

RESEARCH_DECISIONS = Path(
    "output/investment_alpha_research_lab/"
    "alpha_research_promotion_decisions.csv"
)

RESEARCH_METRICS = Path(
    "output/investment_alpha_research_lab/"
    "alpha_research_engine_metrics.csv"
)

RESEARCH_REPORT = Path(
    "output/investment_alpha_research_lab/"
    "alpha_research_lab_report.json"
)

ENSEMBLE_REPORT = Path(
    "output/investment_alpha_ensemble/"
    "alpha_ensemble_report.json"
)

ENSEMBLE_SCORES = Path(
    "output/investment_alpha_ensemble/"
    "alpha_ensemble_scores.csv"
)

ALPHA_ENGINE_SUMMARY = Path(
    "output/investment_alpha_engines/"
    "alpha_engine_summary.csv"
)

ALPHA_ENGINE_LATEST = Path(
    "output/investment_alpha_engines/"
    "alpha_engine_latest.csv"
)


def load_learning_inputs() -> dict:
    """Load existing and v3.1 learning inputs safely."""
    return {
        "performance": safe_read_json(
            PERFORMANCE_REPORT
        ),
        "equity_curve": safe_read_csv(
            EQUITY_CURVE
        ),
        "broker_fills": safe_read_csv(
            BROKER_FILLS
        ),
        "attribution": safe_read_csv(
            ATTRIBUTION
        ),
        "risk": safe_read_json(
            RISK_REPORT
        ),
        "research_decisions": safe_read_csv(
            RESEARCH_DECISIONS
        ),
        "research_metrics": safe_read_csv(
            RESEARCH_METRICS
        ),
        "research_report": safe_read_json(
            RESEARCH_REPORT
        ),
        "ensemble_report": safe_read_json(
            ENSEMBLE_REPORT
        ),
        "ensemble_scores": safe_read_csv(
            ENSEMBLE_SCORES
        ),
        "alpha_engine_summary": safe_read_csv(
            ALPHA_ENGINE_SUMMARY
        ),
        "alpha_engine_latest": safe_read_csv(
            ALPHA_ENGINE_LATEST
        ),
    }
