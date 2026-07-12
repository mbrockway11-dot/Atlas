"""Research Variant Implementation Planner v1 loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


IMPLEMENTATION_QUEUE = Path(
    "output/investment_variant_decisions/"
    "implementation_queue.csv"
)

DECISION_LEDGER = Path(
    "output/investment_variant_decisions/"
    "variant_decision_ledger.csv"
)

VARIANT_REGISTRY = Path(
    "output/investment_validated_variants/"
    "validated_variant_registry.csv"
)


def load_implementation_planner_inputs() -> dict[str, Any]:
    """Load manually approved variant-planning inputs."""
    return {
        "implementation_queue": safe_read_csv(
            IMPLEMENTATION_QUEUE
        ),
        "decision_ledger": safe_read_csv(
            DECISION_LEDGER
        ),
        "variant_registry": safe_read_csv(
            VARIANT_REGISTRY
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
