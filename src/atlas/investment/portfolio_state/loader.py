
"""Portfolio State v4 loaders.

Portfolio State v4 is MTM/broker-authoritative only.
"""

from __future__ import annotations

from pathlib import Path

from atlas.common.io import safe_read_csv, safe_read_json


MTM_REPORT = Path("output/investment_mark_to_market/mark_to_market_report.json")
MTM_POSITIONS = Path("output/investment_mark_to_market/positions.csv")
BROKER_POSITIONS = Path("output/investment_paper_broker/paper_broker_positions.csv")
BROKER_FILLS = Path("output/investment_paper_broker/paper_broker_fills.csv")
BROKER_CASH_LEDGER = Path("output/investment_paper_broker/paper_broker_cash_ledger.csv")


def load_portfolio_state_inputs() -> dict:
    return {
        "mtm_report": safe_read_json(MTM_REPORT),
        "mtm_positions": safe_read_csv(MTM_POSITIONS),
        "broker_positions": safe_read_csv(BROKER_POSITIONS),
        "broker_fills": safe_read_csv(BROKER_FILLS),
        "broker_cash_ledger": safe_read_csv(BROKER_CASH_LEDGER),
    }
