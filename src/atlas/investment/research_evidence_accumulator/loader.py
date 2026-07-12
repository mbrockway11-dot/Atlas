"""Research Evidence Accumulator source loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


SOURCE_PATHS = {
    "program_registry": Path(
        "output/investment_research_program_manager/"
        "research_program_registry.csv"
    ),
    "execution_runs": Path(
        "output/investment_research_experiment_execution/"
        "experiment_execution_runs.csv"
    ),
    "variant_results": Path(
        "output/investment_research_experiment_execution/"
        "experiment_variant_results.csv"
    ),
    "fold_results": Path(
        "output/investment_research_experiment_execution/"
        "experiment_fold_results.csv"
    ),
    "acceptance_results": Path(
        "output/investment_research_experiment_execution/"
        "experiment_acceptance_results.csv"
    ),
    "evidence_summary": Path(
        "output/investment_research_experiment_execution/"
        "experiment_evidence_summary.csv"
    ),
    "execution_report": Path(
        "output/investment_research_experiment_execution/"
        "experiment_execution_report.json"
    ),
    "compiler_report": Path(
        "output/investment_atlas_compiler/"
        "atlas_compiler_report.json"
    ),
}


def load_accumulator_sources() -> dict[str, Any]:
    return {
        name: (
            safe_read_json(path)
            if path.suffix.lower() == ".json"
            else safe_read_csv(path)
        )
        for name, path in SOURCE_PATHS.items()
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

    return payload if isinstance(
        payload,
        dict,
    ) else {}
