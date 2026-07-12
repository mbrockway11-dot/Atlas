"""Variant Review Board v1 configuration."""

from __future__ import annotations

from pathlib import Path


VERSION = "variant_review_board_v1"
SCHEMA_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_variant_review"
)

BOARD_CSV = (
    OUTPUT_DIR
    / "variant_review_board.csv"
)

APPROVED_CSV = (
    OUTPUT_DIR
    / "approved_variants.csv"
)

HELD_CSV = (
    OUTPUT_DIR
    / "held_variants.csv"
)

REJECTED_CSV = (
    OUTPUT_DIR
    / "rejected_variants.csv"
)

MORE_RESEARCH_CSV = (
    OUTPUT_DIR
    / "variants_requiring_more_research.csv"
)

REVIEW_QUEUE_CSV = (
    OUTPUT_DIR
    / "variant_review_queue.csv"
)

IMPLEMENTATION_BACKLOG_CSV = (
    OUTPUT_DIR
    / "implementation_backlog.csv"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "variant_review_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "variant_review_report.md"
)

ALLOWED_DECISIONS = {
    "APPROVE",
    "HOLD",
    "REJECT",
    "REQUEST_MORE_RESEARCH",
}

MIN_APPROVE_VALIDATION_SCORE = 0.85
MIN_APPROVE_FOLD_WIN_RATE = 0.65
MIN_APPROVE_RETENTION_RATIO = 0.30
MIN_APPROVE_MEAN_ADVANTAGE = 0.005
MIN_APPROVE_SHARPE_ADVANTAGE = 0.15
MIN_APPROVE_DRAWDOWN_IMPROVEMENT = 0.05
MIN_APPROVE_FOLDS = 4
MIN_APPROVE_CANDIDATE_TRADES = 50

MIN_HOLD_SCORE = 60.0
MIN_RESEARCH_SCORE = 45.0

MAX_COMPLEXITY_SCORE = 1.0
