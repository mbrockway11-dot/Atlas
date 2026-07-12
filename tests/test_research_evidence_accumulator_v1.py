"""Tests for Atlas Research Evidence Accumulator v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.research_evidence_accumulator.accumulator import (
    build_accumulated_evidence,
)
from atlas.investment.research_evidence_accumulator.analysis import (
    calculate_consistency,
    calculate_contradictions,
    calculate_decay,
    calculate_sufficiency,
)
from atlas.investment.research_evidence_accumulator.history import (
    merge_run_history,
    merge_variant_history,
)


def run_history() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "run_id": "RUN-1",
            "experiment_id": "EXP-1",
            "research_program_id": (
                "RPROG-1"
            ),
            "parent_engine_id": "engine_v1",
            "run_status": "COMPLETED",
            "completed_at": (
                "2026-01-01T00:00:00+00:00"
            ),
            "state_hash": "a" * 64,
            "fold_count": 6,
        },
        {
            "run_id": "RUN-2",
            "experiment_id": "EXP-1",
            "research_program_id": (
                "RPROG-1"
            ),
            "parent_engine_id": "engine_v1",
            "run_status": "COMPLETED",
            "completed_at": (
                "2026-02-01T00:00:00+00:00"
            ),
            "state_hash": "b" * 64,
            "fold_count": 6,
        },
    ])


def variant_history() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "run_id": "RUN-1",
            "experiment_id": "EXP-1",
            "research_program_id": (
                "RPROG-1"
            ),
            "experiment_variant_id": (
                "VAR-1"
            ),
            "source_candidate_id": (
                "RCAND-1"
            ),
            "gate_expression": (
                "ALLOW_SIGNAL = NOT "
                "(trend_state == 'NEUTRAL')"
            ),
            "baseline_trade_count": 100,
            "candidate_trade_count": 70,
            "retention_ratio": 0.70,
            "mean_return_advantage": 0.02,
            "sharpe_advantage": 0.30,
            "drawdown_improvement": 0.10,
            "fold_count": 6,
            "fold_win_rate": 0.83333333,
            "acceptance_passed": True,
            "result_status": "PASS",
        },
        {
            "run_id": "RUN-2",
            "experiment_id": "EXP-1",
            "research_program_id": (
                "RPROG-1"
            ),
            "experiment_variant_id": (
                "VAR-1"
            ),
            "source_candidate_id": (
                "RCAND-1"
            ),
            "gate_expression": (
                "ALLOW_SIGNAL = NOT "
                "(trend_state == 'NEUTRAL')"
            ),
            "baseline_trade_count": 110,
            "candidate_trade_count": 75,
            "retention_ratio": 0.68181818,
            "mean_return_advantage": 0.018,
            "sharpe_advantage": 0.25,
            "drawdown_improvement": 0.08,
            "fold_count": 6,
            "fold_win_rate": 0.66666667,
            "acceptance_passed": True,
            "result_status": "PASS",
        },
    ])


def program_registry() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "research_program_id": (
                "RPROG-1"
            ),
            "current_status": (
                "VALIDATING"
            ),
            "is_blocked": False,
        }
    ])


def test_run_history_deduplicates():
    merged = merge_run_history(
        run_history(),
        run_history().iloc[[0]],
    )

    assert len(merged) == 2


def test_variant_history_deduplicates():
    merged = merge_variant_history(
        variant_history(),
        variant_history().iloc[[0]],
    )

    assert len(merged) == 2


def test_consistency_detects_repeatable_positive_results():
    result = calculate_consistency(
        variant_history()
    )

    assert len(result) == 1

    assert float(
        result.iloc[0][
            "consistency_score"
        ]
    ) >= 0.60


def test_contradiction_rate_is_zero_for_same_direction():
    result = calculate_contradictions(
        variant_history()
    )

    assert float(
        result.iloc[0][
            "contradiction_rate"
        ]
    ) == 0.0


def test_decay_is_not_material_for_stable_results():
    result = calculate_decay(
        variant_history(),
        run_history(),
    )

    assert (
        result.iloc[0][
            "decay_status"
        ]
        == "STABLE"
    )


def test_sample_sufficiency_passes():
    result = calculate_sufficiency(
        variant_history(),
        run_history(),
    )

    assert bool(
        result.iloc[0][
            "evidence_sufficient"
        ]
    )


def test_accumulator_identifies_durable_variant():
    bundle = build_accumulated_evidence(
        program_registry=(
            program_registry()
        ),
        run_history=run_history(),
        variant_history=(
            variant_history()
        ),
    )

    variant = bundle[
        "variant_evidence"
    ].iloc[0]

    assert (
        variant[
            "durability_status"
        ]
        == "DURABLE"
    )


def test_accumulator_recommends_evidence_accumulating():
    bundle = build_accumulated_evidence(
        program_registry=(
            program_registry()
        ),
        run_history=run_history(),
        variant_history=(
            variant_history()
        ),
    )

    recommendation = bundle[
        "recommendations"
    ].iloc[0]

    assert (
        recommendation[
            "recommendation"
        ]
        == "RECOMMEND_EVIDENCE_ACCUMULATING"
    )


def test_accumulator_never_authorizes_transition():
    bundle = build_accumulated_evidence(
        program_registry=(
            program_registry()
        ),
        run_history=run_history(),
        variant_history=(
            variant_history()
        ),
    )

    assert not bundle[
        "recommendations"
    ][
        "program_transition_authorized"
    ].astype(bool).any()

    assert not bundle[
        "variant_evidence"
    ][
        "implementation_authorized"
    ].astype(bool).any()

    assert not bundle[
        "variant_evidence"
    ][
        "production_eligible"
    ].astype(bool).any()
