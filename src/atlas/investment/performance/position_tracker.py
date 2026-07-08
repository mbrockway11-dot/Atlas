
"""Paper position tracker."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


PORTFOLIO_CSV = Path("output/investment_paper_trading/paper_portfolio.csv")
LEDGER_CSV = Path("output/investment_paper_trading/paper_trade_ledger.csv")


def load_paper_portfolio() -> pd.DataFrame:
    if not PORTFOLIO_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(PORTFOLIO_CSV)


def load_paper_ledger() -> pd.DataFrame:
    if not LEDGER_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(LEDGER_CSV)


def summarize_positions(portfolio: pd.DataFrame) -> dict:
    if portfolio.empty:
        return {
            "position_count": 0,
            "risky_weight": 0.0,
            "cash_weight": 1.0,
            "reserved_cash_weight": 0.0,
        }

    risky = portfolio[~portfolio["asset"].isin(["CASH", "RESERVED_CASH"])]
    cash = portfolio[portfolio["asset"] == "CASH"]
    reserved = portfolio[portfolio["asset"] == "RESERVED_CASH"]

    return {
        "position_count": int(len(risky)),
        "risky_weight": round(float(risky["paper_weight"].sum()), 6) if not risky.empty else 0.0,
        "cash_weight": round(float(cash["paper_weight"].sum()), 6) if not cash.empty else 0.0,
        "reserved_cash_weight": round(float(reserved["paper_weight"].sum()), 6) if not reserved.empty else 0.0,
    }
