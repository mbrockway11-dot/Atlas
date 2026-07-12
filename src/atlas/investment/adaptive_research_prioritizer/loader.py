"""Adaptive Research Prioritizer source loading."""

from __future__ import annotations

from typing import Any

from atlas.investment.artifacts import (
    artifact_path,
    load_csv,
    load_json,
)


SOURCE_ARTIFACTS = {
    "research_priorities": "meta_research_priorities",
    "hypothesis_library": "meta_hypotheses",
    "failure_modes": "meta_failure_modes",
    "family_gaps": "meta_family_gaps",
    "feature_interactions": "meta_feature_interactions",
    "experiment_registry": "experiment_registry",
    "experiment_observations": "experiment_observations",
    "experiment_metrics": "experiment_metrics",
    "graph_nodes": "knowledge_graph_nodes",
    "graph_edges": "knowledge_graph_edges",
    "graph_metrics": "knowledge_graph_metrics",
    "validated_variants": "validated_variant_registry",
    "variant_decisions": "variant_decision_ledger",
    "implementation_queue": "variant_implementation_queue",
    "scheduler": "research_scheduler_schedule",
    "regime_report": "regime_report",
    "fusion_report": "macro_regime_fusion_report",
    "compiler_report": "atlas_compiler_report",
}

SOURCE_PATHS = {
    name: artifact_path(artifact)
    for name, artifact in SOURCE_ARTIFACTS.items()
}

JSON_SOURCES = {
    "regime_report",
    "fusion_report",
    "compiler_report",
}


def load_prioritizer_sources() -> dict[str, Any]:
    """Load all available prioritizer evidence."""
    return {
        name: (
            load_json(artifact)
            if name in JSON_SOURCES
            else load_csv(artifact)
        )
        for name, artifact in SOURCE_ARTIFACTS.items()
    }
