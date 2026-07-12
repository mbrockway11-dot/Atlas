"""Atlas Experiment Registry source loading."""

from __future__ import annotations

from typing import Any

from atlas.investment.artifacts import (
    artifact_path,
    load_csv,
    load_json,
)


SOURCE_ARTIFACTS = {
    "meta_hypotheses": "meta_hypotheses",
    "hypothesis_validation": "hypothesis_validation_results",
    "validated_variants": "validated_variant_registry",
    "variant_review": "variant_review_board",
    "variant_decisions": "variant_decision_ledger",
    "implementation_plans": "variant_implementation_plans",
    "portfolio_promotion_v1": "portfolio_promotion_v1_decision",
    "portfolio_promotion_v2": "portfolio_promotion_v2_decision",
    "orchestrator_history": "research_orchestrator_history",
    "orchestrator_report": "research_orchestrator_report",
    "compiler_report": "atlas_compiler_report",
}

SOURCE_PATHS = {
    name: artifact_path(artifact)
    for name, artifact in SOURCE_ARTIFACTS.items()
}

JSON_SOURCES = {
    "orchestrator_report",
    "compiler_report",
}


def load_experiment_sources() -> dict[str, Any]:
    """Load all available experiment evidence."""
    return {
        name: (
            load_json(artifact)
            if name in JSON_SOURCES
            else load_csv(artifact)
        )
        for name, artifact in SOURCE_ARTIFACTS.items()
    }
