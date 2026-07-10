
"""Broker Ledger v4.1 loaders."""

from __future__ import annotations

from pathlib import Path

from atlas.common.io import safe_read_csv, safe_read_json


PAPER_BROKER_REPORT = Path(
    "output/investment_paper_broker/paper_broker_report.json"
)
PAPER_BROKER_POSITIONS = Path(
    "output/investment_paper_broker/paper_broker_positions.csv"
)
PAPER_BROKER_FILLS = Path(
    "output/investment_paper_broker/paper_broker_fills.csv"
)
PAPER_BROKER_CASH_LEDGER = Path(
    "output/investment_paper_broker/paper_broker_cash_ledger.csv"
)
EXECUTION_FILLS = Path(
    "output/investment_execution_engine/execution_fills.csv"
)


def load_broker_ledger_inputs() -> dict:
    return {
        "paper_broker_report": safe_read_json(PAPER_BROKER_REPORT),
        "paper_broker_positions": safe_read_csv(PAPER_BROKER_POSITIONS),
        "paper_broker_fills": safe_read_csv(PAPER_BROKER_FILLS),
        "paper_broker_cash_ledger": safe_read_csv(PAPER_BROKER_CASH_LEDGER),
        "execution_fills": safe_read_csv(EXECUTION_FILLS),
    }
