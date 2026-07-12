"""Atlas Research Experiment Execution Lab v1 configuration."""

from __future__ import annotations

from pathlib import Path


VERSION = "atlas_research_experiment_execution_v1"
SCHEMA_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_research_experiment_execution"
)

RUNS_CSV = (
    OUTPUT_DIR
    / "experiment_execution_runs.csv"
)

FOLD_RESULTS_CSV = (
    OUTPUT_DIR
    / "experiment_fold_results.csv"
)

VARIANT_RESULTS_CSV = (
    OUTPUT_DIR
    / "experiment_variant_results.csv"
)

TRADE_COMPARISON_CSV = (
    OUTPUT_DIR
    / "experiment_trade_comparison.csv"
)

ACCEPTANCE_RESULTS_CSV = (
    OUTPUT_DIR
    / "experiment_acceptance_results.csv"
)

EXCLUSIONS_CSV = (
    OUTPUT_DIR
    / "experiment_exclusions.csv"
)

VALIDATION_CSV = (
    OUTPUT_DIR
    / "experiment_execution_validation.csv"
)

EVIDENCE_SUMMARY_CSV = (
    OUTPUT_DIR
    / "experiment_evidence_summary.csv"
)

STATE_JSON = (
    OUTPUT_DIR
    / "experiment_execution_state.json"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "experiment_execution_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "experiment_execution_report.md"
)

SOURCE = VERSION

ELIGIBLE_PROGRAM_STATUS = "EXPERIMENT_DESIGNED"

HISTORICAL_TRADES_PATH = Path(
    "output/investment_alpha_engines/"
    "historical_alpha_engine_non_overlapping_trades.csv"
)

HISTORICAL_FEATURES_PATH = Path(
    "output/investment_alpha/"
    "market_feature_history.csv"
)

OBSERVATION_SEARCH_PATHS = (
    HISTORICAL_TRADES_PATH,
    Path(
        "output/investment_hypothesis_validation/"
        "walk_forward_trades.csv"
    ),
    Path(
        "output/investment_hypothesis_validation/"
        "hypothesis_validation_trades.csv"
    ),
    Path(
        "output/investment_alpha_research/"
        "research_trades.csv"
    ),
    Path(
        "output/investment_alpha_research_lab/"
        "research_trades.csv"
    ),
)

ENGINE_COLUMN_CANDIDATES = (
    "engine_id",
    "parent_engine_id",
    "engine_name",
)

TIMESTAMP_COLUMN_CANDIDATES = (
    "timestamp",
    "entry_time",
    "date",
    "signal_date",
)

RETURN_COLUMN_CANDIDATES = (
    "trade_return",
    "strategy_return",
    "net_return",
    "return",
    "forward_return",
    "realized_return",
)

TRADE_ID_COLUMN_CANDIDATES = (
    "trade_id",
    "signal_id",
    "observation_id",
)

MINIMUM_OBSERVATION_COUNT = 30

REQUIRED_DESIGN_CHECKS = {
    "PROGRAM_STATUS_ELIGIBLE",
    "PROGRAM_NOT_BLOCKED",
    "PARENT_ENGINE_PRESENT",
    "PROGRAM_MEMBERS_PRESENT",
    "PROGRAM_DIMENSIONS_PRESENT",
    "NO_UNRESOLVED_CONFLICTS",
}

