"""Tests for Research Variant Implementation Planner v1."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from atlas.investment.variant_implementation_planner.artifacts import (
    build_acceptance_criteria,
    build_engineering_backlog,
    build_rollback_plan,
    build_target_files,
    build_test_plan,
)
from atlas.investment.variant_implementation_planner.builder import (
    build_implementation_plans,
)
from atlas.investment.variant_implementation_planner.storage import (
    merge_plans,
)


def queue() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "variant_id": "VAR-ONE",
            "variant_name": (
                "momentum_only_drawdown_low_v1"
            ),
            "parent_engine_id": (
                "cross_sectional_momentum_v1"
            ),
            "gate_expression": (
                "ALLOW_SIGNAL = "
                "(drawdown_from_90d_high == 'LOW')"
            ),
            "board_rank": 1,
            "board_score": 74.3,
            "validation_score": 1.0,
            "fold_win_rate": 0.83,
            "candidate_trade_count": 90,
            "retention_ratio": 0.54,
            "mean_return_advantage": 0.034,
            "sharpe_advantage": 0.48,
            "drawdown_improvement": 0.28,
        }
    ])


def ledger(
    decision: str = "APPROVED",
) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "variant_id": "VAR-ONE",
            "manual_decision": decision,
            "manual_reviewer": (
                "Michael Elvis Brockway"
            ),
            "manual_rationale": (
                "Approved for research implementation."
            ),
            "approval_version": (
                "variant-review-v1"
            ),
        }
    ])


def registry() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "variant_id": "VAR-ONE",
            "variant_name": (
                "momentum_only_drawdown_low_v1"
            ),
            "hypothesis_id": "HYP-ONE",
            "parent_engine_id": (
                "cross_sectional_momentum_v1"
            ),
            "parent_engine_family": (
                "momentum"
            ),
            "gate_mode": (
                "INCLUDE_ONLY_WHEN"
            ),
            "feature": (
                "drawdown_from_90d_high"
            ),
            "target_state": "LOW",
            "gate_expression": (
                "ALLOW_SIGNAL = "
                "(drawdown_from_90d_high == 'LOW')"
            ),
        }
    ])


def test_only_manually_approved_variants_are_planned():
    approved = build_implementation_plans(
        queue(),
        ledger("APPROVED"),
        registry(),
    )

    rejected = build_implementation_plans(
        queue(),
        ledger("REJECTED"),
        registry(),
    )

    assert len(approved) == 1
    assert rejected.empty


def test_plan_never_authorizes_implementation():
    plans = build_implementation_plans(
        queue(),
        ledger(),
        registry(),
    )

    assert not plans[
        "implementation_authorized"
    ].astype(bool).any()

    assert not plans[
        "production_eligible"
    ].astype(bool).any()

    assert not plans[
        "execution_instruction"
    ].astype(bool).any()


def test_engineering_artifacts_are_created():
    plans = build_implementation_plans(
        queue(),
        ledger(),
        registry(),
    )

    assert len(
        build_target_files(plans)
    ) >= 5

    assert len(
        build_test_plan(plans)
    ) >= 10

    assert len(
        build_acceptance_criteria(
            plans
        )
    ) >= 10

    assert len(
        build_rollback_plan(plans)
    ) >= 6


def test_backlog_remains_unauthorized():
    plans = build_implementation_plans(
        queue(),
        ledger(),
        registry(),
    )

    backlog = build_engineering_backlog(
        plans
    )

    assert not backlog[
        "implementation_authorized"
    ].astype(bool).any()

    assert not backlog[
        "production_eligible"
    ].astype(bool).any()


def test_plan_ids_are_deterministic():
    first = build_implementation_plans(
        queue(),
        ledger(),
        registry(),
    )

    second = build_implementation_plans(
        queue(),
        ledger(),
        registry(),
    )

    assert (
        first["plan_id"].tolist()
        == second["plan_id"].tolist()
    )


def test_plan_storage_is_idempotent(
    tmp_path: Path,
):
    incoming = build_implementation_plans(
        queue(),
        ledger(),
        registry(),
    )

    merged, conflicts, stats = (
        merge_plans(
            pd.DataFrame(),
            incoming,
        )
    )

    assert conflicts.empty
    assert (
        stats["inserted_rows"]
        == 1
    )

    second, second_conflicts, second_stats = (
        merge_plans(
            merged,
            incoming,
        )
    )

    assert second_conflicts.empty
    assert (
        second_stats[
            "unchanged_rows"
        ]
        == 1
    )

    assert len(second) == 1
