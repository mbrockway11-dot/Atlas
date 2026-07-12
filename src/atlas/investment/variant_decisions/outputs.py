"""Manual Variant Decision Ledger output projections."""

from __future__ import annotations

import pandas as pd


def build_decision_outputs(
    ledger: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Split ledger into decision-specific outputs."""
    if ledger is None or ledger.empty:
        empty = pd.DataFrame()

        return {
            "approved": empty,
            "rejected": empty,
            "archived": empty,
            "deferred": empty,
            "revisit": empty,
            "implementation_queue": empty,
        }

    approved = select_decision(
        ledger,
        "APPROVED",
    )

    rejected = select_decision(
        ledger,
        "REJECTED",
    )

    archived = select_decision(
        ledger,
        "ARCHIVED",
    )

    deferred = select_decision(
        ledger,
        "DEFERRED",
    )

    revisit = select_decision(
        ledger,
        "REVISIT_LATER",
    )

    implementation_queue = (
        build_implementation_queue(
            approved
        )
    )

    return {
        "approved": approved,
        "rejected": rejected,
        "archived": archived,
        "deferred": deferred,
        "revisit": revisit,
        "implementation_queue": (
            implementation_queue
        ),
    }


def select_decision(
    ledger: pd.DataFrame,
    decision: str,
) -> pd.DataFrame:
    return ledger[
        ledger[
            "manual_decision"
        ].astype(str)
        .str.upper()
        .eq(decision)
    ].copy().reset_index(
        drop=True
    )


def build_implementation_queue(
    approved: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "queue_rank",
        "variant_id",
        "variant_name",
        "parent_engine_id",
        "gate_expression",
        "board_rank",
        "board_score",
        "validation_score",
        "fold_win_rate",
        "candidate_trade_count",
        "retention_ratio",
        "mean_return_advantage",
        "sharpe_advantage",
        "drawdown_improvement",
        "manual_reviewer",
        "manual_rationale",
        "approval_version",
        "implementation_status",
        "implementation_owner",
        "implementation_branch",
        "implementation_commit",
        "queue_status",
        "implementation_authorized",
        "production_eligible",
        "execution_instruction",
    ]

    if approved.empty:
        return pd.DataFrame(
            columns=columns
        )

    queue = approved[
        [
            "variant_id",
            "variant_name",
            "parent_engine_id",
            "gate_expression",
            "board_rank",
            "board_score",
            "validation_score",
            "fold_win_rate",
            "candidate_trade_count",
            "retention_ratio",
            "mean_return_advantage",
            "sharpe_advantage",
            "drawdown_improvement",
            "manual_reviewer",
            "manual_rationale",
            "approval_version",
            "implementation_status",
            "implementation_owner",
            "implementation_branch",
            "implementation_commit",
        ]
    ].copy()

    queue = queue.sort_values(
        [
            "board_rank",
            "board_score",
            "variant_id",
        ],
        ascending=[
            True,
            False,
            True,
        ],
        kind="stable",
    ).reset_index(drop=True)

    queue.insert(
        0,
        "queue_rank",
        range(
            1,
            len(queue) + 1,
        ),
    )

    queue["queue_status"] = (
        "APPROVED_AWAITING_IMPLEMENTATION"
    )

    queue[
        "implementation_authorized"
    ] = False

    queue[
        "production_eligible"
    ] = False

    queue[
        "execution_instruction"
    ] = False

    return queue[
        columns
    ]
