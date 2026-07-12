"""Research Hypothesis Validation Lab v1 loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


HYPOTHESES_CSV = Path(
    "output/investment_meta_research/"
    "hypothesis_library.csv"
)

TRADES_CSV = Path(
    "output/investment_alpha_engines/"
    "historical_alpha_engine_non_overlapping_trades.csv"
)

MARKET_HISTORY_CSV = Path(
    "output/investment_alpha/"
    "market_feature_history.csv"
)


def load_validation_inputs() -> dict[str, Any]:
    """Load hypotheses, historical trades, and market features."""
    return {
        "hypotheses": safe_read_csv(
            HYPOTHESES_CSV
        ),
        "trades": safe_read_csv(
            TRADES_CSV
        ),
        "market_history": safe_read_csv(
            MARKET_HISTORY_CSV
        ),
    }


def safe_read_csv(
    path: Path,
) -> pd.DataFrame:
    if (
        not path.exists()
        or not path.is_file()
        or path.stat().st_size == 0
    ):
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
        OSError,
    ):
        return pd.DataFrame()
