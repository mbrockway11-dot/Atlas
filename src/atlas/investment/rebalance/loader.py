
"""Rebalance Engine v4 loaders."""

from __future__ import annotations

from pathlib import Path

from atlas.common.io import safe_read_csv, safe_read_json


ALPHA_PORTFOLIO = Path("output/investment_alpha/alpha_portfolio.csv")
PORTFOLIO_STATE = Path("output/investment_portfolio_state/portfolio_state.json")
PORTFOLIO_HOLDINGS = Path("output/investment_portfolio_state/portfolio_holdings.csv")
RISK_REPORT = Path("output/investment_risk/risk_engine_report.json")
LEARNING_REPORT = Path("output/investment_learning/learning_report.json")


def load_rebalance_inputs() -> dict:
    return {
        "alpha_portfolio": safe_read_csv(ALPHA_PORTFOLIO),
        "portfolio_state": safe_read_json(PORTFOLIO_STATE),
        "portfolio_holdings": safe_read_csv(PORTFOLIO_HOLDINGS),
        "risk": safe_read_json(RISK_REPORT),
        "learning": safe_read_json(LEARNING_REPORT),
    }
