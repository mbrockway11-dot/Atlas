"""Research Program Manager source loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


SOURCE_PATHS = {
    "consolidated_programs": Path(
        "output/investment_research_candidate_consolidator/"
        "consolidated_research_programs.csv"
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
    "consolidator_report": Path(
        "output/investment_research_candidate_consolidator/"
        "research_candidate_consolidator_report.json"
    ),
    "experiment_registry": Path(
        "output/investment_experiment_registry/"
        "experiment_registry.csv"
    ),
    "experiment_observations": Path(
        "output/investment_experiment_registry/"
        "experiment_observations.csv"
    ),
    "validated_variants": Path(
        "output/investment_validated_variants/"
        "validated_variant_registry.csv"
    ),
    "implementation_queue": Path(
        "output/investment_variant_decisions/"
        "implementation_queue.csv"
    ),
    "compiler_report": Path(
        "output/investment_atlas_compiler/"
        "atlas_compiler_report.json"
    ),
}


def load_program_manager_sources() -> dict[str, Any]:
    """Load all available research-program evidence."""
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

    return (
        payload
        if isinstance(payload, dict)
        else {}
    )
