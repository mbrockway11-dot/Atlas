"""Manual Variant Decision Ledger v1 loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


VARIANT_REVIEW_BOARD = Path(
    "output/investment_variant_review/"
    "variant_review_board.csv"
)

VALIDATED_VARIANT_REGISTRY = Path(
    "output/investment_validated_variants/"
    "validated_variant_registry.csv"
)


def load_variant_decision_inputs() -> dict[str, Any]:
    """Load current board and immutable registry state."""
    return {
        "review_board": safe_read_csv(
            VARIANT_REVIEW_BOARD
        ),
        "variant_registry": safe_read_csv(
            VALIDATED_VARIANT_REGISTRY
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
