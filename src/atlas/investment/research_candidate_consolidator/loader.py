"""Research Candidate Consolidator source loading."""

from __future__ import annotations

from typing import Any

from atlas.investment.artifacts import artifact_path, load_csv, load_json


SOURCE_KEYS = {
    "priority_queue": "research_priority_queue",
    "candidate_scores": "research_candidate_scores",
    "score_components": "research_score_components",
    "explanations": "research_priority_explanations",
    "duplication_flags": "research_duplication_flags",
    "failure_modes": "meta_failure_modes",
    "compiler_report": "atlas_compiler_report",
}

SOURCE_PATHS = {
    name: artifact_path(key)
    for name, key in SOURCE_KEYS.items()
}


def load_consolidator_sources() -> dict[str, Any]:
    """Load all candidate consolidation inputs."""
    return {
        name: (
            load_json(key)
            if artifact_path(key).suffix.lower() == ".json"
            else load_csv(key)
        )
        for name, key in SOURCE_KEYS.items()
    }
