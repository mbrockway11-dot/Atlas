"""Research Hypothesis Validation Lab v1 configuration."""

from __future__ import annotations

from pathlib import Path


VERSION = "research_hypothesis_validation_lab_v1"
SCHEMA_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_hypothesis_validation"
)

RESULTS_CSV = (
    OUTPUT_DIR
    / "hypothesis_validation_results.csv"
)

FOLD_RESULTS_CSV = (
    OUTPUT_DIR
    / "hypothesis_validation_folds.csv"
)

TRADE_LEDGER_CSV = (
    OUTPUT_DIR
    / "hypothesis_validation_trade_ledger.csv"
)

VALIDATED_CSV = (
    OUTPUT_DIR
    / "validated_hypotheses.csv"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "hypothesis_validation_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "hypothesis_validation_report.md"
)

SUPPORTED_HYPOTHESIS_TYPES = {
    "FAILURE_MODE_GATE",
    "CONDITIONAL_OPPORTUNITY",
}

MINIMUM_TRAINING_DAYS = 180
TEST_WINDOW_DAYS = 90
STEP_DAYS = 90

MINIMUM_VALID_FOLDS = 3
MINIMUM_BASELINE_TEST_TRADES = 12
MINIMUM_TOTAL_CANDIDATE_TRADES = 30
MINIMUM_RETENTION_RATIO = 0.20

TRANSACTION_COST_BPS = 10.0

MINIMUM_MEAN_RETURN_ADVANTAGE = 0.0025
MINIMUM_PROFIT_FACTOR_ADVANTAGE = 0.10
MINIMUM_SHARPE_ADVANTAGE = 0.10
MINIMUM_DRAWDOWN_IMPROVEMENT = 0.00
MINIMUM_FOLD_WIN_RATE = 0.60

REJECTION_MEAN_ADVANTAGE = 0.0
REJECTION_FOLD_WIN_RATE = 0.40
