"""Validated Variant Registry v1 loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


VALIDATED_HYPOTHESES = Path(
    "output/investment_hypothesis_validation/"
    "validated_hypotheses.csv"
)

HYPOTHESIS_LIBRARY = Path(
    "output/investment_meta_research/"
    "hypothesis_library.csv"
)

VALIDATION_FOLDS = Path(
    "output/investment_hypothesis_validation/"
    "hypothesis_validation_folds.csv"
)

ENGINE_PERFORMANCE = Path(
    "output/investment_alpha_engines/"
    "historical_alpha_engine_performance.csv"
)


def load_variant_registry_inputs() -> dict[str, Any]:
    """Load validated research evidence."""
    return {
        "validated_hypotheses": safe_read_csv(
            VALIDATED_HYPOTHESES
        ),
        "hypothesis_library": safe_read_csv(
            HYPOTHESIS_LIBRARY
        ),
        "validation_folds": safe_read_csv(
            VALIDATION_FOLDS
        ),
        "engine_performance": safe_read_csv(
            ENGINE_PERFORMANCE
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
