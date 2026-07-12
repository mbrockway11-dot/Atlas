"""Atlas Experiment Registry source loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


SOURCE_PATHS = {
    "meta_hypotheses": Path(
        "output/investment_meta_research/"
        "hypothesis_library.csv"
    ),
    "hypothesis_validation": Path(
        "output/investment_hypothesis_validation/"
        "hypothesis_validation_results.csv"
    ),
    "validated_variants": Path(
        "output/investment_validated_variants/"
        "validated_variant_registry.csv"
    ),
    "variant_review": Path(
        "output/investment_variant_review/"
        "variant_review_board.csv"
    ),
    "variant_decisions": Path(
        "output/investment_variant_decisions/"
        "variant_decision_ledger.csv"
    ),
    "implementation_plans": Path(
        "output/"
        "investment_variant_implementation_planner/"
        "variant_implementation_plans.csv"
    ),
    "portfolio_promotion_v1": Path(
        "output/investment_portfolio_promotion_lab/"
        "portfolio_promotion_decision.csv"
    ),
    "portfolio_promotion_v2": Path(
        "output/investment_portfolio_promotion_lab_v2/"
        "walk_forward_promotion_decision.csv"
    ),
    "orchestrator_history": Path(
        "output/investment_research_orchestrator/"
        "orchestrator_run_history.csv"
    ),
    "orchestrator_report": Path(
        "output/investment_research_orchestrator/"
        "execution_report.json"
    ),
    "compiler_report": Path(
        "output/investment_atlas_compiler/"
        "atlas_compiler_report.json"
    ),
}


def load_experiment_sources() -> dict[str, Any]:
    """Load all available experiment evidence."""
    return {
        "meta_hypotheses": safe_read_csv(
            SOURCE_PATHS["meta_hypotheses"]
        ),
        "hypothesis_validation": safe_read_csv(
            SOURCE_PATHS[
                "hypothesis_validation"
            ]
        ),
        "validated_variants": safe_read_csv(
            SOURCE_PATHS[
                "validated_variants"
            ]
        ),
        "variant_review": safe_read_csv(
            SOURCE_PATHS["variant_review"]
        ),
        "variant_decisions": safe_read_csv(
            SOURCE_PATHS[
                "variant_decisions"
            ]
        ),
        "implementation_plans": safe_read_csv(
            SOURCE_PATHS[
                "implementation_plans"
            ]
        ),
        "portfolio_promotion_v1": safe_read_csv(
            SOURCE_PATHS[
                "portfolio_promotion_v1"
            ]
        ),
        "portfolio_promotion_v2": safe_read_csv(
            SOURCE_PATHS[
                "portfolio_promotion_v2"
            ]
        ),
        "orchestrator_history": safe_read_csv(
            SOURCE_PATHS[
                "orchestrator_history"
            ]
        ),
        "orchestrator_report": safe_read_json(
            SOURCE_PATHS[
                "orchestrator_report"
            ]
        ),
        "compiler_report": safe_read_json(
            SOURCE_PATHS[
                "compiler_report"
            ]
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
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        OSError,
    ):
        return {}

    return (
        payload
        if isinstance(payload, dict)
        else {}
    )
