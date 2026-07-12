"""Canonical Atlas research job registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResearchJobSpec:
    """One schedulable Atlas research stage."""

    job_id: str
    title: str
    command: str
    output_path: Path
    dependencies: tuple[str, ...]
    priority: str
    stale_after_hours: float
    enabled: bool = True
    category: str = "research"


JOBS = (
    ResearchJobSpec(
        job_id="alpha_engines",
        title="Run Alpha Engines",
        command=(
            "python scripts/run_alpha_engines.py"
        ),
        output_path=Path(
            "output/investment_alpha_engines/"
            "alpha_engine_report.json"
        ),
        dependencies=(),
        priority="CRITICAL",
        stale_after_hours=26.0,
        category="alpha",
    ),
    ResearchJobSpec(
        job_id="macro_intelligence",
        title="Update Macro Intelligence",
        command=(
            "python scripts/update_macro_intelligence.py"
        ),
        output_path=Path(
            "output/investment_macro_intelligence/"
            "macro_intelligence_report.json"
        ),
        dependencies=(),
        priority="CRITICAL",
        stale_after_hours=26.0,
        category="market_context",
    ),
    ResearchJobSpec(
        job_id="regime_intelligence",
        title="Update Regime Intelligence",
        command=(
            "python scripts/update_regime_intelligence.py"
        ),
        output_path=Path(
            "output/investment_regime_intelligence/"
            "regime_intelligence_report.json"
        ),
        dependencies=(
            "alpha_engines",
        ),
        priority="CRITICAL",
        stale_after_hours=26.0,
        category="market_context",
    ),
    ResearchJobSpec(
        job_id="macro_regime_fusion",
        title="Update Macro-Regime Fusion",
        command=(
            "python scripts/update_macro_regime_fusion.py"
        ),
        output_path=Path(
            "output/investment_macro_regime_fusion/"
            "macro_regime_fusion_report.json"
        ),
        dependencies=(
            "macro_intelligence",
            "regime_intelligence",
        ),
        priority="CRITICAL",
        stale_after_hours=26.0,
        category="market_context",
    ),
    ResearchJobSpec(
        job_id="historical_alpha_engines",
        title="Run Historical Alpha Engines",
        command=(
            "python scripts/run_historical_alpha_engines.py"
        ),
        output_path=Path(
            "output/investment_alpha_engines/"
            "historical_alpha_engine_report.json"
        ),
        dependencies=(
            "alpha_engines",
        ),
        priority="HIGH",
        stale_after_hours=168.0,
        category="historical_validation",
    ),
    ResearchJobSpec(
        job_id="historical_alpha_validation",
        title="Validate Historical Alpha Engines",
        command=(
            "python scripts/"
            "validate_historical_alpha_engines.py"
        ),
        output_path=Path(
            "output/investment_alpha_engines/"
            "historical_alpha_engine_validation.json"
        ),
        dependencies=(
            "historical_alpha_engines",
        ),
        priority="HIGH",
        stale_after_hours=168.0,
        category="historical_validation",
    ),
    ResearchJobSpec(
        job_id="alpha_research_lab",
        title="Run Alpha Research Lab",
        command=(
            "python scripts/run_alpha_research_lab.py"
        ),
        output_path=Path(
            "output/investment_alpha_research_lab/"
            "alpha_research_lab_report.json"
        ),
        dependencies=(
            "historical_alpha_validation",
            "macro_regime_fusion",
        ),
        priority="HIGH",
        stale_after_hours=168.0,
        category="research",
    ),
    ResearchJobSpec(
        job_id="alpha_ensemble",
        title="Update Alpha Ensemble",
        command=(
            "python scripts/update_alpha_ensemble.py"
        ),
        output_path=Path(
            "output/investment_alpha_ensemble/"
            "alpha_ensemble_report.json"
        ),
        dependencies=(
            "alpha_engines",
            "alpha_research_lab",
            "macro_regime_fusion",
        ),
        priority="CRITICAL",
        stale_after_hours=26.0,
        category="ensemble",
    ),
    ResearchJobSpec(
        job_id="learning_engine",
        title="Update Learning Engine",
        command=(
            "python scripts/update_learning_engine.py"
        ),
        output_path=Path(
            "output/investment_learning/"
            "learning_report.json"
        ),
        dependencies=(
            "alpha_research_lab",
            "alpha_ensemble",
        ),
        priority="HIGH",
        stale_after_hours=26.0,
        category="learning",
    ),
    ResearchJobSpec(
        job_id="ensemble_intelligence_v7",
        title="Update Ensemble Intelligence v7",
        command=(
            "python scripts/"
            "update_ensemble_intelligence_v7.py"
        ),
        output_path=Path(
            "output/investment_alpha_ensemble/"
            "ensemble_v7_audit.json"
        ),
        dependencies=(
            "alpha_ensemble",
            "learning_engine",
            "macro_regime_fusion",
        ),
        priority="CRITICAL",
        stale_after_hours=26.0,
        category="ensemble",
    ),
    ResearchJobSpec(
        job_id="governance_snapshots",
        title="Update Governance Snapshots",
        command=(
            "python scripts/"
            "update_governance_snapshots.py"
        ),
        output_path=Path(
            "output/investment_governance_snapshots/"
            "governance_snapshots_report.json"
        ),
        dependencies=(
            "ensemble_intelligence_v7",
            "learning_engine",
        ),
        priority="HIGH",
        stale_after_hours=26.0,
        category="governance",
    ),
    ResearchJobSpec(
        job_id="meta_research",
        title="Run Meta Research Engine",
        command=(
            "python scripts/run_meta_research_engine.py"
        ),
        output_path=Path(
            "output/investment_meta_research/"
            "meta_research_report.json"
        ),
        dependencies=(
            "governance_snapshots",
            "historical_alpha_validation",
        ),
        priority="MEDIUM",
        stale_after_hours=168.0,
        category="research",
    ),
    ResearchJobSpec(
        job_id="hypothesis_validation",
        title="Run Hypothesis Validation Lab",
        command=(
            "python scripts/"
            "run_hypothesis_validation_lab.py"
        ),
        output_path=Path(
            "output/investment_hypothesis_validation/"
            "hypothesis_validation_report.json"
        ),
        dependencies=(
            "meta_research",
            "historical_alpha_validation",
        ),
        priority="MEDIUM",
        stale_after_hours=168.0,
        category="research",
    ),
    ResearchJobSpec(
        job_id="validated_variant_registry",
        title="Update Validated Variant Registry",
        command=(
            "python scripts/"
            "update_validated_variant_registry.py"
        ),
        output_path=Path(
            "output/investment_validated_variants/"
            "validated_variant_registry_report.json"
        ),
        dependencies=(
            "hypothesis_validation",
        ),
        priority="MEDIUM",
        stale_after_hours=168.0,
        category="variants",
    ),
    ResearchJobSpec(
        job_id="variant_review_board",
        title="Run Variant Review Board",
        command=(
            "python scripts/run_variant_review_board.py"
        ),
        output_path=Path(
            "output/investment_variant_review/"
            "variant_review_report.json"
        ),
        dependencies=(
            "validated_variant_registry",
            "governance_snapshots",
            "learning_engine",
        ),
        priority="MEDIUM",
        stale_after_hours=168.0,
        category="variants",
    ),
    ResearchJobSpec(
        job_id="variant_decision_ledger",
        title="Synchronize Variant Decision Ledger",
        command=(
            "python scripts/"
            "update_variant_decision_ledger.py"
        ),
        output_path=Path(
            "output/investment_variant_decisions/"
            "variant_decision_report.json"
        ),
        dependencies=(
            "variant_review_board",
        ),
        priority="MEDIUM",
        stale_after_hours=168.0,
        category="variants",
    ),
    ResearchJobSpec(
        job_id="variant_implementation_planner",
        title="Run Variant Implementation Planner",
        command=(
            "python scripts/"
            "run_variant_implementation_planner.py"
        ),
        output_path=Path(
            "output/"
            "investment_variant_implementation_planner/"
            "variant_implementation_planner_report.json"
        ),
        dependencies=(
            "variant_decision_ledger",
        ),
        priority="LOW",
        stale_after_hours=168.0,
        category="variants",
    ),
    ResearchJobSpec(
        job_id="portfolio_optimizer",
        title="Update Portfolio Optimizer",
        command=(
            "python scripts/"
            "update_portfolio_optimizer_v2.py"
        ),
        output_path=Path(
            "output/investment_portfolio_optimizer/"
            "portfolio_optimizer_report.json"
        ),
        dependencies=(
            "ensemble_intelligence_v7",
            "macro_regime_fusion",
        ),
        priority="CRITICAL",
        stale_after_hours=26.0,
        category="portfolio",
    ),
    ResearchJobSpec(
        job_id="portfolio_promotion_lab_v1",
        title="Run Portfolio Promotion Lab v1",
        command=(
            "python scripts/"
            "run_portfolio_promotion_lab.py"
        ),
        output_path=Path(
            "output/investment_portfolio_promotion_lab/"
            "portfolio_promotion_report.json"
        ),
        dependencies=(
            "portfolio_optimizer",
        ),
        priority="HIGH",
        stale_after_hours=168.0,
        category="portfolio",
    ),
    ResearchJobSpec(
        job_id="portfolio_promotion_lab_v2",
        title="Run Portfolio Promotion Lab v2",
        command=(
            "python scripts/"
            "run_portfolio_promotion_lab_v2.py"
        ),
        output_path=Path(
            "output/investment_portfolio_promotion_lab_v2/"
            "portfolio_promotion_v2_report.json"
        ),
        dependencies=(
            "portfolio_optimizer",
            "portfolio_promotion_lab_v1",
        ),
        priority="HIGH",
        stale_after_hours=168.0,
        category="portfolio",
    ),
    ResearchJobSpec(
        job_id="atlas_compiler",
        title="Update Atlas Compiler",
        command=(
            "python scripts/update_atlas_compiler.py"
        ),
        output_path=Path(
            "output/investment_atlas_compiler/"
            "atlas_compiler_report.json"
        ),
        dependencies=(
            "macro_regime_fusion",
            "ensemble_intelligence_v7",
            "governance_snapshots",
            "variant_implementation_planner",
            "portfolio_optimizer",
            "portfolio_promotion_lab_v2",
        ),
        priority="CRITICAL",
        stale_after_hours=26.0,
        category="compiler",
    ),
    ResearchJobSpec(
        job_id="atlas_state_api",
        title="Validate Atlas State API",
        command=(
            "python scripts/"
            "validate_atlas_state_api.py"
        ),
        output_path=Path(
            "output/investment_state_api/"
            "state_api_validation.json"
        ),
        dependencies=(
            "atlas_compiler",
        ),
        priority="CRITICAL",
        stale_after_hours=26.0,
        category="api",
    ),
)


JOB_MAP = {
    job.job_id: job
    for job in JOBS
}
