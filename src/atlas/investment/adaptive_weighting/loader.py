
"""Adaptive Weighting v4 loaders."""

from __future__ import annotations

from pathlib import Path

from atlas.common.io import safe_read_csv, safe_read_json


ENSEMBLE_ALLOCATIONS = Path("output/investment_alpha_ensemble/alpha_ensemble_allocations.csv")
ENSEMBLE_REPORT = Path("output/investment_alpha_ensemble/alpha_ensemble_report.json")
STRATEGY_REGISTRY = Path("output/investment_strategy_registry/strategy_registry.csv")
STRATEGY_STATE = Path("output/investment_strategy_registry/strategy_registry_state.json")
LEARNING_REPORT = Path("output/investment_learning/learning_report.json")
PERFORMANCE_REPORT = Path("output/investment_performance/performance_report.json")


def load_adaptive_weighting_inputs() -> dict:
    return {
        "ensemble_allocations": safe_read_csv(ENSEMBLE_ALLOCATIONS),
        "ensemble_report": safe_read_json(ENSEMBLE_REPORT),
        "registry": safe_read_csv(STRATEGY_REGISTRY),
        "strategy_state": safe_read_json(STRATEGY_STATE),
        "learning": safe_read_json(LEARNING_REPORT),
        "performance": safe_read_json(PERFORMANCE_REPORT),
    }
