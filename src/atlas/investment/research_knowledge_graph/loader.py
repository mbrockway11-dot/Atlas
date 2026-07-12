"""Research Knowledge Graph source loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


SOURCE_PATHS = {
    "experiments": Path(
        "output/investment_experiment_registry/"
        "experiment_registry.csv"
    ),
    "observations": Path(
        "output/investment_experiment_registry/"
        "experiment_observations.csv"
    ),
    "metrics": Path(
        "output/investment_experiment_registry/"
        "experiment_metrics.csv"
    ),
    "relationships": Path(
        "output/investment_experiment_registry/"
        "experiment_relationships.csv"
    ),
    "statuses": Path(
        "output/investment_experiment_registry/"
        "experiment_status_history.csv"
    ),
    "orchestrator_runs": Path(
        "output/investment_experiment_registry/"
        "experiment_orchestrator_runs.csv"
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
    "compiler_report": Path(
        "output/investment_atlas_compiler/"
        "atlas_compiler_report.json"
    ),
}


def load_graph_sources() -> dict[str, Any]:
    """Load all graph source records."""
    return {
        "experiments": safe_read_csv(
            SOURCE_PATHS["experiments"]
        ),
        "observations": safe_read_csv(
            SOURCE_PATHS["observations"]
        ),
        "metrics": safe_read_csv(
            SOURCE_PATHS["metrics"]
        ),
        "relationships": safe_read_csv(
            SOURCE_PATHS["relationships"]
        ),
        "statuses": safe_read_csv(
            SOURCE_PATHS["statuses"]
        ),
        "orchestrator_runs": safe_read_csv(
            SOURCE_PATHS[
                "orchestrator_runs"
            ]
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
