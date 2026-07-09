
"""Alpha Portfolio v3 loaders."""

from __future__ import annotations

from pathlib import Path

from atlas.common.io import safe_read_csv, safe_read_json


ADAPTIVE_WEIGHTS = Path("output/investment_adaptive_weighting/adaptive_weights.csv")
ADAPTIVE_REPORT = Path("output/investment_adaptive_weighting/adaptive_weighting_report.json")
STRATEGY_REGISTRY = Path("output/investment_strategy_registry/strategy_registry.csv")
LEARNING_REPORT = Path("output/investment_learning/learning_report.json")
PORTFOLIO_STATE = Path("output/investment_portfolio_state/portfolio_state.json")


def load_alpha_portfolio_inputs() -> dict:
    return {
        "adaptive_weights": safe_read_csv(ADAPTIVE_WEIGHTS),
        "adaptive_report": safe_read_json(ADAPTIVE_REPORT),
        "strategy_registry": safe_read_csv(STRATEGY_REGISTRY),
        "learning": safe_read_json(LEARNING_REPORT),
        "portfolio_state": safe_read_json(PORTFOLIO_STATE),
    }
