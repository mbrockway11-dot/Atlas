
"""Trade Safety Governor loaders."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


EXECUTION_ORDERS = Path("output/investment_execution/execution_order_intents.csv")
SIMULATOR_REPORT = Path("output/investment_execution_simulator/execution_simulator_report.json")
PERFORMANCE_REPORT = Path("output/investment_performance/performance_report.json")
LEARNING_REPORT = Path("output/investment_learning/learning_report.json")
DECISION_REPORT = Path("output/investment_decision/decision_engine_report.json")
RISK_REPORT = Path("output/investment_risk/risk_engine_report.json")


def load_csv(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


def load_json(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_inputs() -> dict:
    return {
        "orders": load_csv(EXECUTION_ORDERS),
        "simulation": load_json(SIMULATOR_REPORT),
        "performance": load_json(PERFORMANCE_REPORT),
        "learning": load_json(LEARNING_REPORT),
        "decision": load_json(DECISION_REPORT),
        "risk": load_json(RISK_REPORT),
    }
