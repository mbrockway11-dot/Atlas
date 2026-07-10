
"""Investment Intelligence Layer v1 loaders."""

from __future__ import annotations

from pathlib import Path

from atlas.common.io import safe_read_csv, safe_read_json


PATHS = {
    "market_features": Path(
        "output/investment_market_features/market_features_report.json"
    ),
    "alpha_hypotheses": Path(
        "output/investment_alpha/alpha_hypotheses_report.json"
    ),
    "alpha_validation": Path(
        "output/investment_alpha/alpha_validation_report.json"
    ),
    "alpha_ensemble": Path(
        "output/investment_alpha_ensemble/alpha_ensemble_report.json"
    ),
    "alpha_ensemble_scores": Path(
        "output/investment_alpha_ensemble/alpha_ensemble_scores.csv"
    ),
    "adaptive_weighting": Path(
        "output/investment_adaptive_weighting/adaptive_weighting_report.json"
    ),
    "adaptive_weights": Path(
        "output/investment_adaptive_weighting/adaptive_weights.csv"
    ),
    "alpha_portfolio": Path(
        "output/investment_alpha/alpha_portfolio_report.json"
    ),
    "alpha_portfolio_csv": Path(
        "output/investment_alpha/alpha_portfolio.csv"
    ),
    "rebalance": Path(
        "output/investment_rebalance/rebalance_report.json"
    ),
    "rebalance_orders": Path(
        "output/investment_rebalance/rebalance_orders.csv"
    ),
    "execution_planner": Path(
        "output/investment_execution/execution_planner_report.json"
    ),
    "safety": Path(
        "output/investment_safety/trade_safety_report.json"
    ),
    "execution_engine": Path(
        "output/investment_execution_engine/execution_engine_report.json"
    ),
    "paper_broker": Path(
        "output/investment_paper_broker/paper_broker_report.json"
    ),
    "broker_ledger": Path(
        "output/investment_broker_ledger/broker_ledger_report.json"
    ),
    "broker_positions": Path(
        "output/investment_broker_ledger/broker_ledger_positions.csv"
    ),
    "mark_to_market": Path(
        "output/investment_mark_to_market/mark_to_market_report.json"
    ),
    "mtm_positions": Path(
        "output/investment_mark_to_market/positions.csv"
    ),
    "portfolio_state": Path(
        "output/investment_portfolio_state/portfolio_state.json"
    ),
    "performance": Path(
        "output/investment_performance/performance_report.json"
    ),
    "performance_attribution": Path(
        "output/investment_performance/performance_attribution.csv"
    ),
    "learning": Path(
        "output/investment_learning/learning_report.json"
    ),
    "strategy_registry": Path(
        "output/investment_strategy_registry/strategy_registry_report.json"
    ),
    "strategy_registry_csv": Path(
        "output/investment_strategy_registry/strategy_registry.csv"
    ),
    "risk": Path(
        "output/investment_risk/risk_engine_report.json"
    ),
    "position_manager": Path(
        "output/investment_position_manager/position_manager_report.json"
    ),
    "action_engine": Path(
        "output/investment_action_engine/action_engine_report.json"
    ),
    "core": Path(
        "output/atlas_core/atlas_core_report.json"
    ),
    "prior_intelligence": Path(
        "output/investment_intelligence/investment_intelligence_report.json"
    ),
}


CSV_KEYS = {
    "alpha_ensemble_scores",
    "adaptive_weights",
    "alpha_portfolio_csv",
    "rebalance_orders",
    "broker_positions",
    "mtm_positions",
    "performance_attribution",
    "strategy_registry_csv",
}


def load_investment_intelligence_inputs() -> dict:
    loaded = {}

    for key, path in PATHS.items():
        if key in CSV_KEYS:
            loaded[key] = safe_read_csv(path)
        else:
            loaded[key] = safe_read_json(path)

    return loaded
