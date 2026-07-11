"""Meta Research Engine v1 input loaders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


TRADES_CSV = Path(
    "output/investment_alpha_engines/"
    "historical_alpha_engine_non_overlapping_trades.csv"
)

MARKET_HISTORY_CSV = Path(
    "output/investment_alpha/"
    "market_feature_history.csv"
)

ENGINE_PERFORMANCE_CSV = Path(
    "output/investment_alpha_engines/"
    "historical_alpha_engine_performance.csv"
)

ENGINE_INDEPENDENCE_CSV = Path(
    "output/investment_alpha_engines/"
    "historical_alpha_engine_independence.csv"
)

RESEARCH_DECISIONS_CSV = Path(
    "output/investment_alpha_research_lab/"
    "alpha_research_promotion_decisions.csv"
)

GOVERNANCE_SNAPSHOTS_CSV = Path(
    "output/investment_governance_snapshots/"
    "engine_governance_snapshots.csv"
)

REGIME_HISTORY_CSV = Path(
    "output/investment_regime_intelligence/"
    "regime_history.csv"
)

FUSION_HISTORY_CSV = Path(
    "output/investment_macro_regime_fusion/"
    "macro_regime_fusion_history.csv"
)

LEARNING_MEMORY_CSV = Path(
    "output/investment_learning/"
    "strategy_memory_summary.csv"
)

RESEARCH_REPORT_JSON = Path(
    "output/investment_alpha_research_lab/"
    "alpha_research_lab_report.json"
)


def load_meta_research_inputs() -> dict[str, Any]:
    """Load all available research evidence safely."""
    return {
        "trades": safe_read_csv(
            TRADES_CSV
        ),
        "market_history": safe_read_csv(
            MARKET_HISTORY_CSV
        ),
        "engine_performance": safe_read_csv(
            ENGINE_PERFORMANCE_CSV
        ),
        "engine_independence": safe_read_csv(
            ENGINE_INDEPENDENCE_CSV
        ),
        "research_decisions": safe_read_csv(
            RESEARCH_DECISIONS_CSV
        ),
        "governance_snapshots": safe_read_csv(
            GOVERNANCE_SNAPSHOTS_CSV
        ),
        "regime_history": safe_read_csv(
            REGIME_HISTORY_CSV
        ),
        "fusion_history": safe_read_csv(
            FUSION_HISTORY_CSV
        ),
        "learning_memory": safe_read_csv(
            LEARNING_MEMORY_CSV
        ),
        "research_report": safe_read_json(
            RESEARCH_REPORT_JSON
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


def safe_read_json(
    path: Path,
) -> dict:
    if (
        not path.exists()
        or not path.is_file()
        or path.stat().st_size == 0
    ):
        return {}

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8-sig"
            )
        )
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        OSError,
    ):
        return {}
