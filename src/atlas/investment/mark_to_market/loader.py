
"""Mark-to-Market v4 loaders.

Broker Ledger v4.1 is the sole source for cash and positions.
"""

from __future__ import annotations

from pathlib import Path

from atlas.common.io import safe_read_csv, safe_read_json


BROKER_LEDGER_REPORT = Path(
    "output/investment_broker_ledger/broker_ledger_report.json"
)
BROKER_LEDGER_POSITIONS = Path(
    "output/investment_broker_ledger/broker_ledger_positions.csv"
)
BROKER_LEDGER_TRADES = Path(
    "output/investment_broker_ledger/broker_ledger_trades.csv"
)
PRICE_DATA = Path("output/price_data.csv")


def load_mark_to_market_inputs() -> dict:
    return {
        "broker_ledger_report": safe_read_json(
            BROKER_LEDGER_REPORT
        ),
        "broker_ledger_positions": safe_read_csv(
            BROKER_LEDGER_POSITIONS
        ),
        "broker_ledger_trades": safe_read_csv(
            BROKER_LEDGER_TRADES
        ),
        "price_data": safe_read_csv(PRICE_DATA),
    }
