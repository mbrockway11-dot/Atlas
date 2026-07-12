"""Atlas Research Evidence Accumulator v1 configuration."""

from __future__ import annotations

from pathlib import Path


VERSION = "atlas_research_evidence_accumulator_v1"
SCHEMA_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_research_evidence_accumulator"
)

EXPERIMENT_EVIDENCE_CSV = (
    OUTPUT_DIR
    / "accumulated_experiment_evidence.csv"
)

VARIANT_EVIDENCE_CSV = (
    OUTPUT_DIR
    / "accumulated_variant_evidence.csv"
)

RUN_LINEAGE_CSV = (
    OUTPUT_DIR
    / "evidence_run_lineage.csv"
)

CONSISTENCY_CSV = (
    OUTPUT_DIR
    / "evidence_consistency.csv"
)

DECAY_CSV = (
    OUTPUT_DIR
    / "evidence_decay.csv"
)

CONTRADICTIONS_CSV = (
    OUTPUT_DIR
    / "evidence_contradictions.csv"
)

SUFFICIENCY_CSV = (
    OUTPUT_DIR
    / "evidence_sufficiency.csv"
)

RECOMMENDATIONS_CSV = (
    OUTPUT_DIR
    / "evidence_program_recommendations.csv"
)

HISTORY_CSV = (
    OUTPUT_DIR
    / "evidence_history.csv"
)

STATE_JSON = (
    OUTPUT_DIR
    / "research_evidence_accumulator_state.json"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "research_evidence_accumulator_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "research_evidence_accumulator_report.md"
)

SOURCE = VERSION

ELIGIBLE_PROGRAM_STATUSES = {
    "VALIDATING",
    "EVIDENCE_ACCUMULATING",
}

MINIMUM_COMPLETED_RUNS = 2
MINIMUM_DISTINCT_STATE_HASHES = 2
MINIMUM_TOTAL_CANDIDATE_TRADES = 60
MINIMUM_TOTAL_FOLD_COUNT = 6
MINIMUM_RUN_PASS_RATE = 0.60
MINIMUM_FOLD_WIN_RATE = 0.60
MINIMUM_CONSISTENCY_SCORE = 0.60
MAXIMUM_CONTRADICTION_RATE = 0.35
MAXIMUM_DECAY_RATE = 0.25

EVIDENCE_WEIGHTS = {
    "run_pass_rate": 0.20,
    "fold_consistency": 0.18,
    "mean_return_consistency": 0.16,
    "sharpe_consistency": 0.14,
    "drawdown_consistency": 0.12,
    "sample_sufficiency": 0.10,
    "state_diversity": 0.06,
    "recency": 0.04,
}
