"""Atlas Research Experiment Designer v1 configuration."""

from __future__ import annotations

from pathlib import Path


VERSION = "atlas_research_experiment_designer_v1"
SCHEMA_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_research_experiment_designer"
)

DESIGNS_CSV = (
    OUTPUT_DIR
    / "research_experiment_designs.csv"
)

HYPOTHESES_CSV = (
    OUTPUT_DIR
    / "experiment_hypotheses.csv"
)

VARIANTS_CSV = (
    OUTPUT_DIR
    / "experiment_variants.csv"
)

WALK_FORWARD_CSV = (
    OUTPUT_DIR
    / "experiment_walk_forward_plan.csv"
)

METRICS_CSV = (
    OUTPUT_DIR
    / "experiment_metrics.csv"
)

ACCEPTANCE_CSV = (
    OUTPUT_DIR
    / "experiment_acceptance_criteria.csv"
)

DATASETS_CSV = (
    OUTPUT_DIR
    / "experiment_dataset_requirements.csv"
)

RISKS_CSV = (
    OUTPUT_DIR
    / "experiment_risk_register.csv"
)

VALIDATION_CSV = (
    OUTPUT_DIR
    / "experiment_design_validation.csv"
)

STATE_JSON = (
    OUTPUT_DIR
    / "research_experiment_designer_state.json"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "research_experiment_designer_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "research_experiment_designer_report.md"
)

SOURCE = VERSION

ELIGIBLE_PROGRAM_STATUSES = {
    "APPROVED_FOR_DESIGN",
    "EXPERIMENT_DESIGNED",
    "VALIDATING",
    "EVIDENCE_ACCUMULATING",
}

DEFAULT_FOLD_COUNT = 6
DEFAULT_EMBARGO_DAYS = 7
DEFAULT_MIN_TRADES = 30
DEFAULT_MIN_RETENTION_RATIO = 0.25
DEFAULT_MAX_RETENTION_RATIO = 0.85

REQUIRED_METRICS = (
    "trade_count",
    "mean_return",
    "median_return",
    "win_rate",
    "expectancy",
    "sharpe_ratio",
    "max_drawdown",
    "return_to_drawdown",
    "fold_win_rate",
    "retention_ratio",
)


