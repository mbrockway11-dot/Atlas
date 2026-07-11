"""Portfolio Promotion Lab v1 input loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atlas.common.io import (
    safe_read_csv,
    safe_read_json,
)


BASELINE_PORTFOLIO = Path(
    "output/investment_alpha/"
    "alpha_portfolio_latest.csv"
)

BASELINE_REPORT = Path(
    "output/investment_alpha/"
    "alpha_portfolio_report.json"
)

CANDIDATE_PORTFOLIO = Path(
    "output/investment_portfolio_optimizer/"
    "optimized_portfolio.csv"
)

CANDIDATE_REPORT = Path(
    "output/investment_portfolio_optimizer/"
    "portfolio_optimizer_report.json"
)

MARKET_HISTORY = Path(
    "output/investment_alpha/"
    "market_feature_history.csv"
)


def load_promotion_inputs() -> dict[str, Any]:
    """Load baseline, candidate, and historical market inputs."""
    return {
        "baseline_portfolio": safe_read_csv(
            BASELINE_PORTFOLIO
        ),
        "baseline_report": safe_read_json(
            BASELINE_REPORT
        ),
        "candidate_portfolio": safe_read_csv(
            CANDIDATE_PORTFOLIO
        ),
        "candidate_report": safe_read_json(
            CANDIDATE_REPORT
        ),
        "market_history": safe_read_csv(
            MARKET_HISTORY
        ),
    }
