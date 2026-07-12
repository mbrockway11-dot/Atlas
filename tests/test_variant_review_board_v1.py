"""Tests for Variant Review Board v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.variant_review.evidence import (
    build_supporting_maps,
)
from atlas.investment.variant_review.outputs import (
    split_review_outputs,
)
from atlas.investment.variant_review.scoring import (
    build_review_board,
)


def registry() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "variant_id": "VAR-STRONG",
            "variant_name": (
                "strong_variant_v1"
            ),
            "hypothesis_id": "HYP-STRONG",
            "hypothesis_type": (
                "FAILURE_MODE_GATE"
            ),
            "parent_engine_id": (
                "trend_continuation_v1"
            ),
            "parent_engine_family": (
                "trend"
            ),
            "gate_mode": "EXCLUDE_WHEN",
            "feature": "volatility_state",
            "target_state": "LOW",
            "gate_expression": (
                "ALLOW_SIGNAL = NOT "
                "(volatility_state == 'LOW')"
            ),
            "validation_score": 1.0,
            "valid_fold_count": 6,
            "candidate_trade_count": 130,
            "retention_ratio": 0.78,
            "fold_win_rate": 0.83,
            "mean_return_advantage": 0.025,
            "sharpe_advantage": 0.50,
            "drawdown_improvement": 0.20,
        },
        {
            "variant_id": "VAR-WEAK",
            "variant_name": (
                "weak_variant_v1"
            ),
            "hypothesis_id": "HYP-WEAK",
            "hypothesis_type": (
                "CONDITIONAL_OPPORTUNITY"
            ),
            "parent_engine_id": (
                "mean_reversion_v1"
            ),
            "parent_engine_family": (
                "mean_reversion"
            ),
            "gate_mode": (
                "INCLUDE_ONLY_WHEN"
            ),
            "feature": "return_30d",
            "target_state": "HIGH",
            "gate_expression": (
                "ALLOW_SIGNAL = "
                "(return_30d == 'HIGH')"
            ),
            "validation_score": 0.70,
            "valid_fold_count": 3,
            "candidate_trade_count": 25,
            "retention_ratio": 0.15,
            "fold_win_rate": 0.33,
            "mean_return_advantage": -0.002,
            "sharpe_advantage": -0.05,
            "drawdown_improvement": -0.02,
        },
    ])


def maps() -> dict:
    return build_supporting_maps(
        validation_folds=pd.DataFrame(),
        research_priorities=pd.DataFrame([
            {
                "source_id": "HYP-STRONG",
                "priority_score": 0.90,
                "research_rank": 1,
            },
            {
                "source_id": "HYP-WEAK",
                "priority_score": 0.40,
                "research_rank": 2,
            },
        ]),
        learning_memory=pd.DataFrame([
            {
                "engine_id": (
                    "trend_continuation_v1"
                ),
                "recency_weighted_reliability": 0.75,
                "decision_stability": 0.90,
                "observation_count": 5,
            }
        ]),
        governance_snapshots=pd.DataFrame([
            {
                "effective_at": (
                    "2026-07-10T00:00:00+00:00"
                ),
                "engine_id": (
                    "trend_continuation_v1"
                ),
                "eligible": True,
                "final_governance_weight": 0.50,
                "regime_suitability": 0.70,
                "fusion_modifier": 1.05,
            }
        ]),
        engine_performance=pd.DataFrame(),
        conflicts=pd.DataFrame(),
    )


def test_board_ranks_strong_variant_first():
    board = build_review_board(
        registry(),
        maps(),
    )

    assert (
        board.iloc[0][
            "variant_id"
        ]
        == "VAR-STRONG"
    )


def test_strong_variant_is_approved():
    board = build_review_board(
        registry(),
        maps(),
    ).set_index("variant_id")

    assert (
        board.loc[
            "VAR-STRONG",
            "recommended_decision",
        ]
        == "APPROVE"
    )


def test_weak_variant_not_approved():
    board = build_review_board(
        registry(),
        maps(),
    ).set_index("variant_id")

    assert (
        board.loc[
            "VAR-WEAK",
            "recommended_decision",
        ]
        != "APPROVE"
    )


def test_board_does_not_activate_production():
    board = build_review_board(
        registry(),
        maps(),
    )

    assert not board[
        "production_eligible"
    ].astype(bool).any()

    assert not board[
        "execution_instruction"
    ].astype(bool).any()


def test_approved_recommendations_enter_backlog():
    board = build_review_board(
        registry(),
        maps(),
    )

    outputs = split_review_outputs(
        board
    )

    assert not outputs[
        "approved"
    ].empty

    assert not outputs[
        "backlog"
    ].empty

    assert not outputs[
        "backlog"
    ][
        "implementation_authorized"
    ].astype(bool).any()


def test_board_is_deterministic():
    first = build_review_board(
        registry(),
        maps(),
    )

    second = build_review_board(
        registry(),
        maps(),
    )

    pd.testing.assert_frame_equal(
        first,
        second,
    )
