"""Variant Review Board v1 loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


VARIANT_REGISTRY = Path(
    "output/investment_validated_variants/"
    "validated_variant_registry.csv"
)

VARIANT_CONFLICTS = Path(
    "output/investment_validated_variants/"
    "validated_variant_conflicts.csv"
)

VALIDATION_FOLDS = Path(
    "output/investment_hypothesis_validation/"
    "hypothesis_validation_folds.csv"
)

RESEARCH_PRIORITIES = Path(
    "output/investment_meta_research/"
    "research_priorities.csv"
)

LEARNING_MEMORY = Path(
    "output/investment_learning/"
    "strategy_memory_summary.csv"
)

GOVERNANCE_SNAPSHOTS = Path(
    "output/investment_governance_snapshots/"
    "engine_governance_snapshots.csv"
)

ENGINE_PERFORMANCE = Path(
    "output/investment_alpha_engines/"
    "historical_alpha_engine_performance.csv"
)


def load_variant_review_inputs() -> dict[str, Any]:
    """Load canonical variant-review evidence."""
    return {
        "registry": safe_read_csv(
            VARIANT_REGISTRY
        ),
        "conflicts": safe_read_csv(
            VARIANT_CONFLICTS
        ),
        "validation_folds": safe_read_csv(
            VALIDATION_FOLDS
        ),
        "research_priorities": safe_read_csv(
            RESEARCH_PRIORITIES
        ),
        "learning_memory": safe_read_csv(
            LEARNING_MEMORY
        ),
        "governance_snapshots": safe_read_csv(
            GOVERNANCE_SNAPSHOTS
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
