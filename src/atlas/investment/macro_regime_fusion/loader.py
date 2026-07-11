"""Macro-Regime Fusion v1 loaders."""

from __future__ import annotations

from pathlib import Path

from atlas.common.io import (
    safe_read_csv,
    safe_read_json,
)


MACRO_REPORT = Path(
    "output/investment_macro_intelligence/"
    "macro_intelligence_report.json"
)

REGIME_REPORT = Path(
    "output/investment_regime_intelligence/"
    "regime_intelligence_report.json"
)

REGIME_SUITABILITY = Path(
    "output/investment_regime_intelligence/"
    "engine_regime_suitability.csv"
)

ALPHA_ENGINE_SUMMARY = Path(
    "output/investment_alpha_engines/"
    "alpha_engine_summary.csv"
)


def load_macro_regime_inputs() -> dict:
    """Load canonical Macro and Regime Intelligence outputs."""
    return {
        "macro_report": safe_read_json(
            MACRO_REPORT
        ),
        "regime_report": safe_read_json(
            REGIME_REPORT
        ),
        "regime_suitability": safe_read_csv(
            REGIME_SUITABILITY
        ),
        "alpha_engine_summary": safe_read_csv(
            ALPHA_ENGINE_SUMMARY
        ),
    }
