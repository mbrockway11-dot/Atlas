"""Portfolio Optimizer v2 input loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from atlas.common.io import (
    safe_read_csv,
    safe_read_json,
)


ENSEMBLE_SCORES = Path(
    "output/investment_alpha_ensemble/"
    "alpha_ensemble_scores.csv"
)

ENSEMBLE_CONTRIBUTIONS = Path(
    "output/investment_alpha_ensemble/"
    "ensemble_v7_contribution_ledger.csv"
)

MARKET_HISTORY = Path(
    "output/investment_alpha/"
    "market_feature_history.csv"
)

MARKET_FEATURES = Path(
    "output/investment_alpha/"
    "market_features.csv"
)

FUSION_REPORT = Path(
    "output/investment_macro_regime_fusion/"
    "macro_regime_fusion_report.json"
)

CURRENT_PORTFOLIO = Path(
    "output/investment_alpha/"
    "alpha_portfolio_latest.csv"
)

APPROVED_UNIVERSE = Path(
    "output/investment_market_universe/"
    "approved_universe.csv"
)


def load_optimizer_inputs() -> dict[str, Any]:
    """Load canonical optimizer inputs safely."""
    return {
        "ensemble_scores": safe_read_csv(
            ENSEMBLE_SCORES
        ),
        "ensemble_contributions": safe_read_csv(
            ENSEMBLE_CONTRIBUTIONS
        ),
        "market_history": safe_read_csv(
            MARKET_HISTORY
        ),
        "market_features": safe_read_csv(
            MARKET_FEATURES
        ),
        "fusion_report": safe_read_json(
            FUSION_REPORT
        ),
        "current_portfolio": safe_read_csv(
            CURRENT_PORTFOLIO
        ),
        "approved_universe": safe_read_csv(
            APPROVED_UNIVERSE
        ),
    }
