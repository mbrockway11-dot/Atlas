"""Tests for Manual Variant Decision Ledger v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.variant_decisions.builder import (
    build_current_ledger_rows,
    merge_preserving_manual_decisions,
)
from atlas.investment.variant_decisions.decisions import (
    record_manual_decision,
)
from atlas.investment.variant_decisions.outputs import (
    build_decision_outputs,
)


def review_board() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "review_rank": 1,
            "variant_id": "VAR-ONE",
            "variant_name": (
                "test_variant_one"
            ),
            "hypothesis_id": "HYP-ONE",
            "parent_engine_id": (
                "trend_continuation_v1"
            ),
            "parent_engine_family": (
                "trend"
            ),
            "feature": (
                "volatility_state"
            ),
            "target_state": "LOW",
            "gate_mode": "EXCLUDE_WHEN",
            "gate_expression": (
                "ALLOW_SIGNAL = NOT "
                "(volatility_state == 'LOW')"
            ),
            "recommended_decision": (
                "APPROVE"
            ),
            "overall_review_score": 75.0,
            "validation_score": 1.0,
            "fold_win_rate": 0.80,
            "candidate_trade_count": 100,
            "retention_ratio": 0.70,
            "mean_return_advantage": 0.02,
            "sharpe_advantage": 0.40,
            "drawdown_improvement": 0.20,
        }
    ])


def registry() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "variant_id": "VAR-ONE",
            "variant_name": (
                "test_variant_one"
            ),
        }
    ])


def test_new_variants_begin_pending():
    ledger = build_current_ledger_rows(
        review_board(),
        registry(),
    )

    assert (
        ledger.iloc[0][
            "manual_decision"
        ]
        == "PENDING"
    )

    assert not bool(
        ledger.iloc[0][
            "implementation_authorized"
        ]
    )


def test_manual_decision_is_preserved():
    incoming = build_current_ledger_rows(
        review_board(),
        registry(),
    )

    existing = incoming.copy()

    existing.loc[
        0,
        "manual_decision",
    ] = "APPROVED"

    existing.loc[
        0,
        "manual_reviewer",
    ] = "Michael Brockway"

    existing.loc[
        0,
        "manual_rationale",
    ] = "Approved for research implementation."

    existing.loc[
        0,
        "manual_decision_locked",
    ] = True

    updated_board = review_board()

    updated_board.loc[
        0,
        "overall_review_score",
    ] = 80.0

    refreshed = build_current_ledger_rows(
        updated_board,
        registry(),
    )

    merged, stats = (
        merge_preserving_manual_decisions(
            existing,
            refreshed,
        )
    )

    assert (
        merged.iloc[0][
            "manual_decision"
        ]
        == "APPROVED"
    )

    assert (
        merged.iloc[0][
            "manual_reviewer"
        ]
        == "Michael Brockway"
    )

    assert (
        float(
            merged.iloc[0][
                "board_score"
            ]
        )
        == 80.0
    )

    assert (
        stats[
            "preserved_manual_rows"
        ]
        == 1
    )


def test_record_decision_appends_history():
    ledger = build_current_ledger_rows(
        review_board(),
        registry(),
    )

    updated, history, record = (
        record_manual_decision(
            ledger=ledger,
            history=pd.DataFrame(),
            variant_id="VAR-ONE",
            decision="APPROVED",
            reviewer=(
                "Michael Brockway"
            ),
            rationale=(
                "Approved for research-only implementation."
            ),
            approval_version="review-v1",
        )
    )

    assert (
        updated.iloc[0][
            "manual_decision"
        ]
        == "APPROVED"
    )

    assert len(history) == 1

    assert (
        record["new_decision"]
        == "APPROVED"
    )


def test_only_approved_variants_enter_queue():
    ledger = build_current_ledger_rows(
        review_board(),
        registry(),
    )

    ledger.loc[
        0,
        "manual_decision",
    ] = "APPROVED"

    outputs = build_decision_outputs(
        ledger
    )

    assert len(
        outputs[
            "implementation_queue"
        ]
    ) == 1

    assert not outputs[
        "implementation_queue"
    ][
        "implementation_authorized"
    ].astype(bool).any()


def test_board_approve_does_not_equal_human_approval():
    ledger = build_current_ledger_rows(
        review_board(),
        registry(),
    )

    assert (
        ledger.iloc[0][
            "board_recommendation"
        ]
        == "APPROVE"
    )

    assert (
        ledger.iloc[0][
            "manual_decision"
        ]
        == "PENDING"
    )


def test_ledger_never_marks_production_eligible():
    ledger = build_current_ledger_rows(
        review_board(),
        registry(),
    )

    assert not ledger[
        "production_eligible"
    ].astype(bool).any()

    assert not ledger[
        "execution_instruction"
    ].astype(bool).any()
