"""Historical Governance Snapshots v1 loaders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


RESEARCH_DECISIONS = Path(
    "output/investment_alpha_research_lab/"
    "alpha_research_promotion_decisions.csv"
)

LEARNING_RECOMMENDATIONS = Path(
    "output/investment_learning/"
    "engine_learning_recommendations.csv"
)

REGIME_SUITABILITY = Path(
    "output/investment_regime_intelligence/"
    "engine_regime_suitability.csv"
)

FUSION_MODIFIERS = Path(
    "output/investment_macro_regime_fusion/"
    "engine_context_modifiers.csv"
)

ENSEMBLE_GOVERNANCE = Path(
    "output/investment_alpha_ensemble/"
    "ensemble_v7_engine_governance.csv"
)

MACRO_REPORT = Path(
    "output/investment_macro_intelligence/"
    "macro_intelligence_report.json"
)

REGIME_REPORT = Path(
    "output/investment_regime_intelligence/"
    "regime_intelligence_report.json"
)

FUSION_REPORT = Path(
    "output/investment_macro_regime_fusion/"
    "macro_regime_fusion_report.json"
)

MARKET_FEATURES = Path(
    "output/investment_alpha/"
    "market_features.csv"
)


def load_snapshot_inputs() -> dict[str, Any]:
    """Load all canonical governance inputs."""
    return {
        "research_decisions": safe_read_csv(
            RESEARCH_DECISIONS
        ),
        "learning_recommendations": safe_read_csv(
            LEARNING_RECOMMENDATIONS
        ),
        "regime_suitability": safe_read_csv(
            REGIME_SUITABILITY
        ),
        "fusion_modifiers": safe_read_csv(
            FUSION_MODIFIERS
        ),
        "ensemble_governance": safe_read_csv(
            ENSEMBLE_GOVERNANCE
        ),
        "macro_report": safe_read_json(
            MACRO_REPORT
        ),
        "regime_report": safe_read_json(
            REGIME_REPORT
        ),
        "fusion_report": safe_read_json(
            FUSION_REPORT
        ),
        "market_features": safe_read_csv(
            MARKET_FEATURES
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
