
"""Execution Planner v3 loaders."""

from __future__ import annotations

from pathlib import Path

from atlas.common.io import safe_read_csv, safe_read_json


REBALANCE_ORDERS = Path("output/investment_rebalance/rebalance_orders.csv")
REBALANCE_REPORT = Path("output/investment_rebalance/rebalance_report.json")
SAFETY_REPORT = Path("output/investment_safety/trade_safety_report.json")


def load_execution_planner_inputs() -> dict:
    return {
        "rebalance_orders": safe_read_csv(REBALANCE_ORDERS),
        "rebalance_report": safe_read_json(REBALANCE_REPORT),
        "safety_report": safe_read_json(SAFETY_REPORT),
    }
