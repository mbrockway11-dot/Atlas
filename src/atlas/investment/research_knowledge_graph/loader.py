"""Research Knowledge Graph source loading."""

from __future__ import annotations

from typing import Any

from atlas.investment.artifacts import (
    artifact_path,
    load_csv,
    load_json,
)


SOURCE_ARTIFACTS = {
    "experiments": "experiment_registry",
    "observations": "experiment_observations",
    "metrics": "experiment_metrics",
    "relationships": "experiment_relationships",
    "statuses": "experiment_status_history",
    "orchestrator_runs": "experiment_orchestrator_runs",
    "variant_decisions": "variant_decision_ledger",
    "implementation_plans": "variant_implementation_plans",
    "compiler_report": "atlas_compiler_report",
}

SOURCE_PATHS = {
    name: artifact_path(artifact)
    for name, artifact in SOURCE_ARTIFACTS.items()
}


def load_graph_sources() -> dict[str, Any]:
    """Load all graph source records."""
    return {
        name: (
            load_json(artifact)
            if name == "compiler_report"
            else load_csv(artifact)
        )
        for name, artifact in SOURCE_ARTIFACTS.items()
    }
