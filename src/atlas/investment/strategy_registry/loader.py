
"""Strategy Registry v3 loaders."""

from __future__ import annotations

from pathlib import Path

from atlas.common.io import safe_read_csv, safe_read_json


LEARNING_REPORT = Path("output/investment_learning/learning_report.json")
LEARNING_SCORECARD = Path("output/investment_learning/strategy_scorecard.csv")
PERFORMANCE_REPORT = Path("output/investment_performance/performance_report.json")
REGISTRY_STATE = Path("output/investment_strategy_registry/strategy_registry_state.json")


def load_strategy_registry_inputs() -> dict:
    return {
        "learning": safe_read_json(LEARNING_REPORT),
        "scorecard": safe_read_csv(LEARNING_SCORECARD),
        "performance": safe_read_json(PERFORMANCE_REPORT),
        "prior_state": safe_read_json(REGISTRY_STATE),
    }
