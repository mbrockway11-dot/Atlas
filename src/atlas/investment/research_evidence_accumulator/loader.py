"""Research Evidence Accumulator source loading."""

from __future__ import annotations

from typing import Any

from atlas.common.io import safe_read_csv, safe_read_json
from atlas.investment.artifacts import artifact_path, load_csv, load_json


SOURCE_KEYS = {
    "program_registry": "research_program_registry",
    "execution_runs": "research_execution_runs",
    "variant_results": "research_execution_variant_results",
    "fold_results": "research_execution_fold_results",
    "acceptance_results": "research_execution_acceptance_results",
    "evidence_summary": "research_execution_evidence_summary",
    "execution_report": "research_execution_report",
    "compiler_report": "atlas_compiler_report",
}

SOURCE_PATHS = {
    name: artifact_path(key)
    for name, key in SOURCE_KEYS.items()
}


def load_accumulator_sources() -> dict[str, Any]:
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
    "load_accumulator_sources",
    "safe_read_csv",
    "safe_read_json",
]
