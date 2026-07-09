
"""Learning Engine v3 loaders."""

from __future__ import annotations

from pathlib import Path

from atlas.common.io import safe_read_csv, safe_read_json


PERFORMANCE_REPORT = Path("output/investment_performance/performance_report.json")
EQUITY_CURVE = Path("output/investment_mark_to_market/equity_curve.csv")
BROKER_FILLS = Path("output/investment_paper_broker/paper_broker_fills.csv")
ATTRIBUTION = Path("output/investment_performance/performance_attribution.csv")
RISK_REPORT = Path("output/investment_risk/risk_engine_report.json")


def load_learning_inputs() -> dict:
    return {
        "performance": safe_read_json(PERFORMANCE_REPORT),
        "equity_curve": safe_read_csv(EQUITY_CURVE),
        "broker_fills": safe_read_csv(BROKER_FILLS),
        "attribution": safe_read_csv(ATTRIBUTION),
        "risk": safe_read_json(RISK_REPORT),
    }
