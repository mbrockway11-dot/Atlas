
"""Strategy Registry loaders."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


SIGIL_SIGNALS = Path("output/investment_adapters/sigil_v32/sigil_v32_strategy_signals.csv")
ALPHA_PORTFOLIO = Path("output/investment_alpha/alpha_portfolio_latest.csv")
CROSS_SECTIONAL_LATEST = Path("output/investment_alpha/cross_sectional_alpha_latest.csv")


def load_csv(path: str | Path) -> pd.DataFrame:
    target = Path(path)
    if not target.exists():
        return pd.DataFrame()
    return pd.read_csv(target)


def load_sigil_v32_signals() -> pd.DataFrame:
    return load_csv(SIGIL_SIGNALS)


def load_alpha_portfolio() -> pd.DataFrame:
    return load_csv(ALPHA_PORTFOLIO)


def load_cross_sectional_latest() -> pd.DataFrame:
    return load_csv(CROSS_SECTIONAL_LATEST)
