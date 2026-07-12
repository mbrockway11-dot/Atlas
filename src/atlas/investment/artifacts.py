"""Canonical Atlas investment artifact registry.

This module owns stable artifact keys and safe key-based reads. Subsystem
business logic remains local; filesystem paths and defensive parsing do not.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from atlas.common.io import safe_read_csv, safe_read_json


ARTIFACTS: dict[str, Path] = {
    # Meta research and validation.
    "meta_hypotheses": Path("output/investment_meta_research/hypothesis_library.csv"),
    "meta_research_priorities": Path("output/investment_meta_research/research_priorities.csv"),
    "meta_failure_modes": Path("output/investment_meta_research/engine_failure_modes.csv"),
    "meta_family_gaps": Path("output/investment_meta_research/engine_family_gaps.csv"),
    "meta_feature_interactions": Path("output/investment_meta_research/feature_interactions.csv"),
    "hypothesis_validation_results": Path("output/investment_hypothesis_validation/hypothesis_validation_results.csv"),
    "validated_hypotheses": Path("output/investment_hypothesis_validation/validated_hypotheses.csv"),
    "hypothesis_validation_folds": Path("output/investment_hypothesis_validation/hypothesis_validation_folds.csv"),
    "historical_alpha_validation_report": Path("output/investment_historical_alpha_validation/historical_alpha_validation_report.json"),
    "historical_alpha_engine_performance": Path("output/investment_alpha_engines/historical_alpha_engine_performance.csv"),

    # Scheduler and orchestration.
    "research_scheduler_schedule": Path("output/investment_research_scheduler/research_schedule.csv"),
    "research_orchestrator_history": Path("output/investment_research_orchestrator/orchestrator_run_history.csv"),
    "research_orchestrator_report": Path("output/investment_research_orchestrator/execution_report.json"),

    # Experiment registry and graph snapshots.
    "experiment_registry": Path("output/investment_experiment_registry/experiment_registry.csv"),
    "experiment_observations": Path("output/investment_experiment_registry/experiment_observations.csv"),
    "experiment_metrics": Path("output/investment_experiment_registry/experiment_metrics.csv"),
    "experiment_artifacts": Path("output/investment_experiment_registry/experiment_artifacts.csv"),
    "experiment_relationships": Path("output/investment_experiment_registry/experiment_relationships.csv"),
    "experiment_status_history": Path("output/investment_experiment_registry/experiment_status_history.csv"),
    "experiment_orchestrator_runs": Path("output/investment_experiment_registry/experiment_orchestrator_runs.csv"),
    "knowledge_graph_nodes": Path("output/investment_research_knowledge_graph/knowledge_graph_nodes.csv"),
    "knowledge_graph_edges": Path("output/investment_research_knowledge_graph/knowledge_graph_edges.csv"),
    "knowledge_graph_metrics": Path("output/investment_research_knowledge_graph/graph_metrics.csv"),

    # Adaptive prioritization and consolidation.
    "research_priority_queue": Path("output/investment_adaptive_research_prioritizer/research_priority_queue.csv"),
    "research_candidate_scores": Path("output/investment_adaptive_research_prioritizer/research_candidate_scores.csv"),
    "research_score_components": Path("output/investment_adaptive_research_prioritizer/research_score_components.csv"),
    "research_priority_explanations": Path("output/investment_adaptive_research_prioritizer/research_priority_explanations.csv"),
    "research_duplication_flags": Path("output/investment_adaptive_research_prioritizer/research_duplication_flags.csv"),
    "consolidated_research_programs": Path("output/investment_research_candidate_consolidator/consolidated_research_programs.csv"),
    "research_program_members": Path("output/investment_research_candidate_consolidator/research_program_members.csv"),
    "research_program_dimensions": Path("output/investment_research_candidate_consolidator/research_program_dimensions.csv"),
    "research_program_conflicts": Path("output/investment_research_candidate_consolidator/research_program_conflicts.csv"),
    "research_candidate_consolidator_report": Path("output/investment_research_candidate_consolidator/research_candidate_consolidator_report.json"),

    # Program manager and experiment design.
    "research_program_registry": Path("output/investment_research_program_manager/research_program_registry.csv"),
    "research_program_history": Path("output/investment_research_program_manager/research_program_history.csv"),
    "research_program_recommendations": Path("output/investment_research_program_manager/research_program_recommendations.csv"),
    "research_program_manager_report": Path("output/investment_research_program_manager/research_program_manager_report.json"),
    "research_experiment_designs": Path("output/investment_research_experiment_designer/research_experiment_designs.csv"),
    "research_experiment_hypotheses": Path("output/investment_research_experiment_designer/experiment_hypotheses.csv"),
    "research_experiment_variants": Path("output/investment_research_experiment_designer/experiment_variants.csv"),
    "research_experiment_walk_forward_plan": Path("output/investment_research_experiment_designer/experiment_walk_forward_plan.csv"),
    "research_experiment_acceptance_criteria": Path("output/investment_research_experiment_designer/experiment_acceptance_criteria.csv"),
    "research_experiment_design_validation": Path("output/investment_research_experiment_designer/experiment_design_validation.csv"),
    "research_experiment_designer_report": Path("output/investment_research_experiment_designer/research_experiment_designer_report.json"),

    # Experiment execution.
    "research_execution_runs": Path("output/investment_research_experiment_execution/experiment_execution_runs.csv"),
    "research_execution_fold_results": Path("output/investment_research_experiment_execution/experiment_fold_results.csv"),
    "research_execution_variant_results": Path("output/investment_research_experiment_execution/experiment_variant_results.csv"),
    "research_execution_acceptance_results": Path("output/investment_research_experiment_execution/experiment_acceptance_results.csv"),
    "research_execution_evidence_summary": Path("output/investment_research_experiment_execution/experiment_evidence_summary.csv"),
    "research_execution_report": Path("output/investment_research_experiment_execution/experiment_execution_report.json"),

    # Accumulated longitudinal evidence.
    "accumulated_experiment_evidence": Path("output/investment_research_evidence_accumulator/accumulated_experiment_evidence.csv"),
    "accumulated_variant_evidence": Path("output/investment_research_evidence_accumulator/accumulated_variant_evidence.csv"),
    "evidence_run_lineage": Path("output/investment_research_evidence_accumulator/evidence_run_lineage.csv"),
    "evidence_consistency": Path("output/investment_research_evidence_accumulator/evidence_consistency.csv"),
    "evidence_decay": Path("output/investment_research_evidence_accumulator/evidence_decay.csv"),
    "evidence_contradictions": Path("output/investment_research_evidence_accumulator/evidence_contradictions.csv"),
    "evidence_sufficiency": Path("output/investment_research_evidence_accumulator/evidence_sufficiency.csv"),
    "evidence_program_recommendations": Path("output/investment_research_evidence_accumulator/evidence_program_recommendations.csv"),
    "evidence_history": Path("output/investment_research_evidence_accumulator/evidence_history.csv"),
    "research_evidence_accumulator_state": Path("output/investment_research_evidence_accumulator/research_evidence_accumulator_state.json"),
    "research_evidence_accumulator_report": Path("output/investment_research_evidence_accumulator/research_evidence_accumulator_report.json"),

    # Variant governance.
    "validated_variant_registry": Path("output/investment_validated_variants/validated_variant_registry.csv"),
    "variant_review_board": Path("output/investment_variant_review/variant_review_board.csv"),
    "variant_review_conflicts": Path("output/investment_variant_review/variant_review_conflicts.csv"),
    "variant_decision_ledger": Path("output/investment_variant_decisions/variant_decision_ledger.csv"),
    "variant_implementation_queue": Path("output/investment_variant_decisions/implementation_queue.csv"),
    "variant_implementation_plans": Path("output/investment_variant_implementation_planner/variant_implementation_plans.csv"),

    # Portfolio, market context, and compiler.
    "portfolio_promotion_v1_decision": Path("output/investment_portfolio_promotion_lab/portfolio_promotion_decision.csv"),
    "portfolio_promotion_v2_decision": Path("output/investment_portfolio_promotion_lab_v2/walk_forward_promotion_decision.csv"),
    "regime_report": Path("output/investment_regime_intelligence/regime_intelligence_report.json"),
    "macro_regime_fusion_report": Path("output/investment_macro_regime_fusion/macro_regime_fusion_report.json"),
    "atlas_compiler_report": Path("output/investment_atlas_compiler/atlas_compiler_report.json"),
}


def artifact_path(name: str) -> Path:
    """Return one registered artifact path."""
    try:
        return ARTIFACTS[name]
    except KeyError as error:
        raise KeyError(f"Unknown Atlas artifact: {name}") from error


def load_csv(name: str) -> pd.DataFrame:
    """Safely load a registered CSV artifact."""
    return safe_read_csv(artifact_path(name))


def load_json(name: str) -> dict[str, Any]:
    """Safely load a registered JSON object artifact."""
    payload = safe_read_json(artifact_path(name))
    return payload if isinstance(payload, dict) else {}


def validate_registry() -> list[str]:
    """Return structural registry errors without touching the filesystem."""
    errors: list[str] = []
    reverse: dict[Path, str] = {}
    for name, path in ARTIFACTS.items():
        if not name or not isinstance(path, Path):
            errors.append(f"INVALID_ENTRY:{name}")
            continue
        normalized = Path(str(path).replace("\\", "/"))
        if normalized in reverse:
            errors.append(f"DUPLICATE_PATH:{reverse[normalized]}:{name}:{normalized}")
        else:
            reverse[normalized] = name
    return errors


__all__ = [
    "ARTIFACTS",
    "artifact_path",
    "load_csv",
    "load_json",
    "validate_registry",
]
