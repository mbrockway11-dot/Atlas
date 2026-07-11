"""Portfolio Promotion Lab v2 input loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atlas.common.io import (
    safe_read_csv,
    safe_read_json,
)


MARKET_HISTORY = Path(
    "output/investment_alpha/"
    "market_feature_history.csv"
)

HISTORICAL_ENGINE_SIGNALS = Path(
    "output/investment_alpha_engines/"
    "historical_alpha_engine_signals.csv"
)

ENGINE_GOVERNANCE = Path(
    "output/investment_alpha_ensemble/"
    "ensemble_v7_engine_governance.csv"
)

APPROVED_UNIVERSE = Path(
    "output/investment_market_universe/"
    "approved_universe.csv"
)

OPTIMIZER_REPORT = Path(
    "output/investment_portfolio_optimizer/"
    "portfolio_optimizer_report.json"
)

GOVERNANCE_SNAPSHOTS = Path(
    "output/investment_governance_snapshots/"
    "engine_governance_snapshots.csv"
)


def load_walk_forward_inputs() -> dict[str, Any]:
    """Load canonical walk-forward research artifacts."""
    return {
        "market_history": safe_read_csv(
            MARKET_HISTORY
        ),
        "historical_engine_signals": safe_read_csv(
            HISTORICAL_ENGINE_SIGNALS
        ),
        "engine_governance": safe_read_csv(
            ENGINE_GOVERNANCE
        ),
        "approved_universe": safe_read_csv(
            APPROVED_UNIVERSE
        ),
        "optimizer_report": safe_read_json(
            OPTIMIZER_REPORT
        ),
        "governance_snapshots": safe_read_csv(
            GOVERNANCE_SNAPSHOTS
        ),
    }

