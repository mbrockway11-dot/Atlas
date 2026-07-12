"""Research Candidate Consolidator source loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


SOURCE_PATHS = {
    "priority_queue": Path(
        "output/investment_adaptive_research_prioritizer/"
        "research_priority_queue.csv"
    ),
    "candidate_scores": Path(
        "output/investment_adaptive_research_prioritizer/"
        "research_candidate_scores.csv"
    ),
    "score_components": Path(
        "output/investment_adaptive_research_prioritizer/"
        "research_score_components.csv"
    ),
    "explanations": Path(
        "output/investment_adaptive_research_prioritizer/"
        "research_priority_explanations.csv"
    ),
    "duplication_flags": Path(
        "output/investment_adaptive_research_prioritizer/"
        "research_duplication_flags.csv"
    ),
    "failure_modes": Path(
        "output/investment_meta_research/"
        "engine_failure_modes.csv"
    ),
    "compiler_report": Path(
        "output/investment_atlas_compiler/"
        "atlas_compiler_report.json"
    ),
}


def load_consolidator_sources() -> dict[str, Any]:
    """Load all candidate consolidation inputs."""
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
