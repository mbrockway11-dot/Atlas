"""Canonical Atlas investment artifact registry.

This module owns shared artifact locations and safe key-based reads. Business
logic remains inside each subsystem; callers use stable keys instead of
repeating paths or defensive CSV/JSON parsing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


ARTIFACTS: dict[str, Path] = {
    # Meta research and validation.
    "meta_hypotheses": Path(
        "output/investment_meta_research/hypothesis_library.csv"
    ),
    "meta_research_priorities": Path(
        "output/investment_meta_research/research_priorities.csv"
    ),
    "meta_failure_modes": Path(
        "output/investment_meta_research/engine_failure_modes.csv"
    ),
    "meta_family_gaps": Path(
        "output/investment_meta_research/engine_family_gaps.csv"
    ),
    "meta_feature_interactions": Path(
        "output/investment_meta_research/feature_interactions.csv"
    ),
    "hypothesis_validation_results": Path(
        "output/investment_hypothesis_validation/"
        "hypothesis_validation_results.csv"
    ),
    "historical_alpha_validation_report": Path(
        "output/investment_historical_alpha_validation/"
        "historical_alpha_validation_report.json"
    ),
    # Variant governance.
    "validated_variant_registry": Path(
        "output/investment_validated_variants/"
        "validated_variant_registry.csv"
    ),
    "variant_review_board": Path(
        "output/investment_variant_review/variant_review_board.csv"
    ),
    "variant_decision_ledger": Path(
        "output/investment_variant_decisions/variant_decision_ledger.csv"
    ),
    "variant_implementation_queue": Path(
        "output/investment_variant_decisions/implementation_queue.csv"
    ),
    "variant_implementation_plans": Path(
        "output/investment_variant_implementation_planner/"
        "variant_implementation_plans.csv"
    ),
    # Portfolio promotion.
    "portfolio_promotion_v1_decision": Path(
        "output/investment_portfolio_promotion_lab/"
        "portfolio_promotion_decision.csv"
    ),
    "portfolio_promotion_v2_decision": Path(
        "output/investment_portfolio_promotion_lab_v2/"
        "walk_forward_promotion_decision.csv"
    ),
    # Scheduler and orchestration.
    "research_scheduler_schedule": Path(
        "output/investment_research_scheduler/research_schedule.csv"
    ),
    "research_orchestrator_history": Path(
        "output/investment_research_orchestrator/"
        "orchestrator_run_history.csv"
    ),
    "research_orchestrator_report": Path(
        "output/investment_research_orchestrator/execution_report.json"
    ),
    # Experiment registry.
    "experiment_registry": Path(
        "output/investment_experiment_registry/experiment_registry.csv"
    ),
    "experiment_observations": Path(
        "output/investment_experiment_registry/experiment_observations.csv"
    ),
    "experiment_metrics": Path(
        "output/investment_experiment_registry/experiment_metrics.csv"
    ),
    "experiment_artifacts": Path(
        "output/investment_experiment_registry/experiment_artifacts.csv"
    ),
    "experiment_relationships": Path(
        "output/investment_experiment_registry/experiment_relationships.csv"
    ),
    "experiment_status_history": Path(
        "output/investment_experiment_registry/experiment_status_history.csv"
    ),
    "experiment_orchestrator_runs": Path(
        "output/investment_experiment_registry/"
        "experiment_orchestrator_runs.csv"
    ),
    # Knowledge graph.
    "knowledge_graph_nodes": Path(
        "output/investment_research_knowledge_graph/"
        "knowledge_graph_nodes.csv"
    ),
    "knowledge_graph_edges": Path(
        "output/investment_research_knowledge_graph/"
        "knowledge_graph_edges.csv"
    ),
    "knowledge_graph_metrics": Path(
        "output/investment_research_knowledge_graph/graph_metrics.csv"
    ),
    # Adaptive prioritizer.
    "research_priority_queue": Path(
        "output/investment_adaptive_research_prioritizer/"
        "research_priority_queue.csv"
    ),
    "research_candidate_scores": Path(
        "output/investment_adaptive_research_prioritizer/"
        "research_candidate_scores.csv"
    ),
    "research_score_components": Path(
        "output/investment_adaptive_research_prioritizer/"
        "research_score_components.csv"
    ),
    "research_priority_explanations": Path(
        "output/investment_adaptive_research_prioritizer/"
        "research_priority_explanations.csv"
    ),
    "research_duplication_flags": Path(
        "output/investment_adaptive_research_prioritizer/"
        "research_duplication_flags.csv"
    ),
    # Candidate consolidator.
    "consolidated_research_programs": Path(
        "output/investment_research_candidate_consolidator/"
        "consolidated_research_programs.csv"
    ),
    "research_program_members": Path(
        "output/investment_research_candidate_consolidator/"
        "research_program_members.csv"
    ),
    "research_program_dimensions": Path(
        "output/investment_research_candidate_consolidator/"
        "research_program_dimensions.csv"
    ),
    "research_program_conflicts": Path(
        "output/investment_research_candidate_consolidator/"
        "research_program_conflicts.csv"
    ),
    "research_candidate_consolidator_report": Path(
        "output/investment_research_candidate_consolidator/"
        "research_candidate_consolidator_report.json"
    ),
    # Program manager and experiment design.
    "research_program_registry": Path(
        "output/investment_research_program_manager/"
        "research_program_registry.csv"
    ),
    "research_experiment_variants": Path(
        "output/investment_research_experiment_designer/"
        "experiment_variants.csv"
    ),
    "research_experiment_designs": Path(
        "output/investment_research_experiment_designer/"
        "experiment_designs.csv"
    ),
    # Market context and compiler.
    "regime_report": Path(
        "output/investment_regime_intelligence/"
        "regime_intelligence_report.json"
    ),
    "macro_regime_fusion_report": Path(
        "output/investment_macro_regime_fusion/"
        "macro_regime_fusion_report.json"
    ),
    "atlas_compiler_report": Path(
        "output/investment_atlas_compiler/atlas_compiler_report.json"
    ),
}


def artifact_path(name: str) -> Path:
    """Return one registered artifact path."""
    try:
        return ARTIFACTS[name]
    except KeyError as error:
        raise KeyError(f"Unknown Atlas artifact: {name}") from error


def load_csv(name: str) -> pd.DataFrame:
    """Safely load a registered CSV artifact."""
    path = artifact_path(name)
    if not path.is_file() or path.stat().st_size == 0:
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


def load_json(name: str) -> dict[str, Any]:
    """Safely load a registered JSON object artifact."""
    path = artifact_path(name)
    if not path.is_file() or path.stat().st_size == 0:
        return {}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return {}

    return payload if isinstance(payload, dict) else {}
