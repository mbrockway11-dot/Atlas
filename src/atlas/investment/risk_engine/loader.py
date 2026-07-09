
"""Risk Engine loaders."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PORTFOLIO_STATE_JSON = Path("output/investment_portfolio_state/portfolio_state.json")
PERFORMANCE_JSON = Path("output/investment_performance/performance_report.json")
LEARNING_JSON = Path("output/investment_learning/learning_report.json")
ACTION_ENGINE_JSON = Path("output/investment_action_engine/action_engine_report.json")
REBALANCE_JSON = Path("output/investment_rebalance/rebalance_report.json")
SAFETY_JSON = Path("output/investment_safety/trade_safety_report.json")


def load_json(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_risk_inputs() -> dict:
    return {
        "portfolio_state": load_json(PORTFOLIO_STATE_JSON),
        "performance": load_json(PERFORMANCE_JSON),
        "learning": load_json(LEARNING_JSON),
        "action_engine": load_json(ACTION_ENGINE_JSON),
        "rebalance": load_json(REBALANCE_JSON),
        "safety": load_json(SAFETY_JSON),
    }
