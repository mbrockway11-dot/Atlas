
"""Execution Engine v3 loaders."""

from __future__ import annotations

import json
from pathlib import Path
import pandas as pd


EXECUTION_INTENTS = Path("output/investment_execution/execution_order_intents.csv")
EXECUTION_LOG = Path("output/investment_execution_engine/execution_log.csv")
SAFETY_REPORT = Path("output/investment_safety/trade_safety_report.json")
RISK_REPORT = Path("output/investment_risk/risk_engine_report.json")


def load_json(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_csv(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(p)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def load_execution_inputs() -> dict:
    return {
        "intents": load_csv(EXECUTION_INTENTS),
        "execution_log": load_csv(EXECUTION_LOG),
        "safety": load_json(SAFETY_REPORT),
        "risk": load_json(RISK_REPORT),
    }
