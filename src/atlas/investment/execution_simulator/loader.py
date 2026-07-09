
"""Execution Simulator loaders."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


ORDER_INTENTS = Path("output/investment_execution/execution_order_intents.csv")
DECISION_REPORT = Path("output/investment_decision/decision_engine_report.json")


def load_order_intents() -> pd.DataFrame:
    target = ORDER_INTENTS

    if not target.exists() or target.stat().st_size == 0:
        return pd.DataFrame()

    try:
        return pd.read_csv(target)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def load_decision_report() -> dict:
    import json

    if not DECISION_REPORT.exists():
        return {}

    try:
        return json.loads(DECISION_REPORT.read_text(encoding="utf-8"))
    except Exception:
        return {}
