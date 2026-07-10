
"""Alpha Ensemble v4 loaders."""

from __future__ import annotations

from pathlib import Path

from atlas.common.io import safe_read_csv, safe_read_json


ALPHA_VALIDATION = Path("output/investment_alpha/alpha_validation_report.json")
BACKTESTS = Path("output/investment_alpha/alpha_backtests.csv")
STRATEGY_REGISTRY = Path("output/investment_strategy_registry/strategy_registry.csv")
LEARNING_REPORT = Path("output/investment_learning/learning_report.json")
PERFORMANCE_REPORT = Path("output/investment_performance/performance_report.json")
MARKET_DIRECTION = Path("output/investment_market_direction/market_direction_report.json")
SIGIL_ADAPTER = Path("output/investment_sigil_v32/sigil_v32_adapter_report.json")


def load_alpha_ensemble_inputs() -> dict:
    return {
        "alpha_validation": safe_read_json(ALPHA_VALIDATION),
        "backtests": safe_read_csv(BACKTESTS),
        "strategy_registry": safe_read_csv(STRATEGY_REGISTRY),
        "learning": safe_read_json(LEARNING_REPORT),
        "performance": safe_read_json(PERFORMANCE_REPORT),
        "market_direction": safe_read_json(MARKET_DIRECTION),
        "sigil_adapter": safe_read_json(SIGIL_ADAPTER),
    }
