"""Research Experiment Designer source loading."""

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
    "program_members": Path(
        "output/investment_research_candidate_consolidator/"
        "research_program_members.csv"
    ),
    "program_dimensions": Path(
        "output/investment_research_candidate_consolidator/"
        "research_program_dimensions.csv"
    ),
    "program_conflicts": Path(
        "output/investment_research_candidate_consolidator/"
        "research_program_conflicts.csv"
    ),
    "candidate_scores": Path(
        "output/investment_adaptive_research_prioritizer/"
        "research_candidate_scores.csv"
    ),
    "historical_validation": Path(
        "output/investment_historical_alpha_validation/"
        "historical_alpha_validation_report.json"
    ),
    "compiler_report": Path(
        "output/investment_atlas_compiler/"
        "atlas_compiler_report.json"
    ),
}


def load_designer_sources() -> dict[str, Any]:
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
