"""Variant Review Board v1 output construction."""

from __future__ import annotations

import pandas as pd


def split_review_outputs(
    board: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Split review recommendations into governance outputs."""
    if board is None or board.empty:
        empty = pd.DataFrame()

        return {
            "approved": empty,
            "held": empty,
            "rejected": empty,
            "more_research": empty,
            "review_queue": empty,
            "backlog": empty,
        }

    approved = select_decision(
        board,
        "APPROVE",
    )

    held = select_decision(
        board,
        "HOLD",
    )

    rejected = select_decision(
        board,
        "REJECT",
    )

    more_research = select_decision(
        board,
        "REQUEST_MORE_RESEARCH",
    )

    review_queue = board[
        [
            "review_rank",
            "variant_id",
            "variant_name",
            "parent_engine_id",
            "feature",
            "target_state",
            "overall_review_score",
            "recommended_decision",
            "decision_reason",
            "review_status",
            "manual_decision",
            "manual_reviewer",
            "manual_rationale",
        ]
    ].copy()

    backlog = approved[
        [
            "review_rank",
            "implementation_priority",
            "variant_id",
            "variant_name",
            "parent_engine_id",
            "gate_expression",
            "overall_review_score",
            "validation_score",
            "fold_win_rate",
            "candidate_trade_count",
            "retention_ratio",
            "mean_return_advantage",
            "sharpe_advantage",
            "drawdown_improvement",
        ]
    ].copy()

    if not backlog.empty:
        backlog.insert(
            0,
            "backlog_rank",
            range(
                1,
                len(backlog) + 1,
            ),
        )

        backlog[
            "backlog_status"
        ] = "AWAITING_MANUAL_APPROVAL"

        backlog[
            "implementation_authorized"
        ] = False

        backlog[
            "execution_instruction"
        ] = False

    return {
        "approved": approved,
        "held": held,
        "rejected": rejected,
        "more_research": (
            more_research
        ),
        "review_queue": review_queue,
        "backlog": backlog,
    }


def select_decision(
    board: pd.DataFrame,
    decision: str,
) -> pd.DataFrame:
    return board[
        board[
            "recommended_decision"
        ].eq(decision)
    ].copy().reset_index(
        drop=True
    )
