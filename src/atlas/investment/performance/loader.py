
"""Performance Engine v3 loaders."""

from __future__ import annotations

from pathlib import Path

from atlas.common.io import safe_read_csv, safe_read_json


MTM_REPORT = Path("output/investment_mark_to_market/mark_to_market_report.json")
MTM_POSITIONS = Path("output/investment_mark_to_market/positions.csv")
EQUITY_CURVE = Path("output/investment_mark_to_market/equity_curve.csv")
BROKER_FILLS = Path("output/investment_paper_broker/paper_broker_fills.csv")
BROKER_LEDGER = Path("output/investment_paper_broker/paper_broker_ledger.csv")
CASH_LEDGER = Path("output/investment_paper_broker/paper_broker_cash_ledger.csv")


def load_performance_inputs() -> dict:
    return {
        "mtm_report": safe_read_json(MTM_REPORT),
        "positions": safe_read_csv(MTM_POSITIONS),
        "equity_curve": safe_read_csv(EQUITY_CURVE),
        "broker_fills": safe_read_csv(BROKER_FILLS),
        "broker_ledger": safe_read_csv(BROKER_LEDGER),
        "cash_ledger": safe_read_csv(CASH_LEDGER),
    }
