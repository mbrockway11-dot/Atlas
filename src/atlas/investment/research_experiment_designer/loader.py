"""Research Experiment Designer source loading."""

from __future__ import annotations

from typing import Any

from atlas.investment.artifacts import artifact_path, load_csv, load_json


SOURCE_KEYS = {
    "program_registry": "research_program_registry",
    "program_members": "research_program_members",
    "program_dimensions": "research_program_dimensions",
    "program_conflicts": "research_program_conflicts",
    "candidate_scores": "research_candidate_scores",
    "historical_validation": "historical_alpha_validation_report",
    "compiler_report": "atlas_compiler_report",
}

SOURCE_PATHS = {
    name: artifact_path(key)
    for name, key in SOURCE_KEYS.items()
}


def load_designer_sources() -> dict[str, Any]:
    """Load all available experiment-design evidence."""
    return {
        name: (
            load_json(key)
            if artifact_path(key).suffix.lower() == ".json"
            else load_csv(key)
        )
        for name, key in SOURCE_KEYS.items()
    }
