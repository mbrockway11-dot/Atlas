"""Research Program Manager source loading."""

from __future__ import annotations

from typing import Any

from atlas.common.io import safe_read_csv, safe_read_json
from atlas.investment.artifacts import artifact_path, load_csv, load_json


SOURCE_KEYS = {
    "consolidated_programs": "consolidated_research_programs",
    "program_members": "research_program_members",
    "program_dimensions": "research_program_dimensions",
    "program_conflicts": "research_program_conflicts",
    "consolidator_report": "research_candidate_consolidator_report",
    "experiment_registry": "experiment_registry",
    "experiment_observations": "experiment_observations",
    "validated_variants": "validated_variant_registry",
    "implementation_queue": "variant_implementation_queue",
    "compiler_report": "atlas_compiler_report",
}

SOURCE_PATHS = {
    name: artifact_path(key)
    for name, key in SOURCE_KEYS.items()
}


def load_program_manager_sources() -> dict[str, Any]:
    """Load all available research-program evidence."""
    return {
        name: (
            load_json(key)
            if artifact_path(key).suffix.lower() == ".json"
            else load_csv(key)
        )
        for name, key in SOURCE_KEYS.items()
    }


__all__ = [
    "SOURCE_KEYS",
    "SOURCE_PATHS",
    "load_program_manager_sources",
    "safe_read_csv",
    "safe_read_json",
]
