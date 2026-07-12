"""Tests for Validated Variant Registry v1."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from atlas.investment.validated_variants.builder import (
    build_variant_specifications,
)
from atlas.investment.validated_variants.storage import (
    merge_registry,
)


def validated_hypotheses() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "hypothesis_id": "HYP-AAA",
            "hypothesis_type": (
                "FAILURE_MODE_GATE"
            ),
            "engine_id": (
                "trend_continuation_v1"
            ),
            "family": "trend",
            "feature": (
                "volatility_state"
            ),
            "state": "LOW",
            "decision": "VALIDATE",
            "validation_score": 1.0,
            "valid_fold_count": 6,
            "baseline_trade_count": 165,
            "candidate_trade_count": 129,
            "retention_ratio": 0.78,
            "fold_win_rate": 0.67,
            "mean_return_advantage": 0.014,
            "profit_factor_advantage": 0.58,
            "sharpe_advantage": 0.49,
            "drawdown_improvement": 0.17,
            "conditions_passed": (
                "mean_return_improved"
            ),
            "hard_failures": "",
        },
        {
            "hypothesis_id": "HYP-BBB",
            "hypothesis_type": (
                "CONDITIONAL_OPPORTUNITY"
            ),
            "engine_id": (
                "cross_sectional_momentum_v1"
            ),
            "family": "momentum",
            "feature": (
                "drawdown_from_90d_high"
            ),
            "state": "LOW",
            "decision": "VALIDATE",
            "validation_score": 1.0,
            "valid_fold_count": 6,
            "baseline_trade_count": 166,
            "candidate_trade_count": 90,
            "retention_ratio": 0.54,
            "fold_win_rate": 0.83,
            "mean_return_advantage": 0.034,
            "profit_factor_advantage": 5.0,
            "sharpe_advantage": 0.48,
            "drawdown_improvement": 0.28,
            "conditions_passed": (
                "mean_return_improved"
            ),
            "hard_failures": "",
        },
    ])


def hypothesis_library() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "hypothesis_id": "HYP-AAA",
            "thesis": "Avoid low volatility.",
            "proposed_test": "Test the gate.",
            "validation_requirement": (
                "Walk-forward validation."
            ),
        },
        {
            "hypothesis_id": "HYP-BBB",
            "thesis": "Use deep drawdowns.",
            "proposed_test": "Test opportunity.",
            "validation_requirement": (
                "Walk-forward validation."
            ),
        },
    ])


def test_only_validated_rows_are_registered():
    frame = validated_hypotheses()

    rejected = frame.iloc[[0]].copy()
    rejected["hypothesis_id"] = (
        "HYP-REJECT"
    )
    rejected["decision"] = "REJECT"

    frame = pd.concat(
        [
            frame,
            rejected,
        ],
        ignore_index=True,
    )

    registry = build_variant_specifications(
        frame,
        hypothesis_library(),
    )

    assert len(registry) == 2

    assert "HYP-REJECT" not in set(
        registry["hypothesis_id"]
    )


def test_variant_ids_are_deterministic():
    first = build_variant_specifications(
        validated_hypotheses(),
        hypothesis_library(),
    )

    second = build_variant_specifications(
        validated_hypotheses(),
        hypothesis_library(),
    )

    assert (
        first["variant_id"].tolist()
        == second["variant_id"].tolist()
    )


def test_gate_modes_are_correct():
    registry = build_variant_specifications(
        validated_hypotheses(),
        hypothesis_library(),
    ).set_index("hypothesis_id")

    assert (
        registry.loc[
            "HYP-AAA",
            "gate_mode",
        ]
        == "EXCLUDE_WHEN"
    )

    assert (
        registry.loc[
            "HYP-BBB",
            "gate_mode",
        ]
        == "INCLUDE_ONLY_WHEN"
    )


def test_variants_require_manual_review():
    registry = build_variant_specifications(
        validated_hypotheses(),
        hypothesis_library(),
    )

    assert registry[
        "manual_approval_required"
    ].astype(bool).all()

    assert not registry[
        "execution_instruction"
    ].astype(bool).any()


def test_registry_is_idempotent(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "registry.csv"
    )

    incoming = build_variant_specifications(
        validated_hypotheses(),
        hypothesis_library(),
    )

    first, conflicts, first_stats = (
        merge_registry(
            incoming=incoming,
            existing_path=path,
        )
    )

    first.to_csv(
        path,
        index=False,
    )

    second, second_conflicts, second_stats = (
        merge_registry(
            incoming=incoming,
            existing_path=path,
        )
    )

    assert len(first) == len(second)
    assert conflicts.empty
    assert second_conflicts.empty
    assert (
        second_stats[
            "inserted_rows"
        ]
        == 0
    )

    assert (
        second_stats[
            "unchanged_rows"
        ]
        == len(incoming)
    )


def test_immutable_conflict_is_detected(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "registry.csv"
    )

    incoming = build_variant_specifications(
        validated_hypotheses(),
        hypothesis_library(),
    )

    incoming.to_csv(
        path,
        index=False,
    )

    changed = incoming.copy()

    changed.loc[
        0,
        "specification_hash",
    ] = "different"

    registry, conflicts, stats = (
        merge_registry(
            incoming=changed,
            existing_path=path,
        )
    )

    assert len(registry) == len(incoming)
    assert not conflicts.empty
    assert (
        stats["conflict_rows"]
        == 1
    )
