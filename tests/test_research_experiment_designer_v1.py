"""Tests for Atlas Research Experiment Designer v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.research_experiment_designer.designer import (
    build_experiment_design_bundle,
)
from atlas.investment.research_experiment_designer.identity import (
    experiment_id,
)


def sources() -> dict:
    return {
        "program_registry": pd.DataFrame([
            {
                "research_program_id": "RPROG-ONE",
                "program_title": (
                    "Trend degradation program"
                ),
                "parent_engine_id": (
                    "trend_continuation_v1"
                ),
                "engine_family": "trend",
                "current_status": (
                    "APPROVED_FOR_DESIGN"
                ),
                "is_blocked": False,
                "program_priority_score": 0.82,
                "cluster_confidence": 0.78,
                "has_conflicts": False,
            },
            {
                "research_program_id": "RPROG-TWO",
                "program_title": "Blocked program",
                "parent_engine_id": "engine_v1",
                "engine_family": "other",
                "current_status": (
                    "APPROVED_FOR_DESIGN"
                ),
                "is_blocked": True,
                "program_priority_score": 0.70,
                "cluster_confidence": 0.60,
                "has_conflicts": True,
            },
        ]),
        "program_members": pd.DataFrame([
            {
                "research_program_id": "RPROG-ONE",
                "candidate_id": "RCAND-ONE",
                "candidate_title": "ATR MID failure",
                "feature_name": "atr_pct_14d",
                "feature_family": "volatility",
                "condition_value": "MID",
                "candidate_score": 0.81,
            },
            {
                "research_program_id": "RPROG-ONE",
                "candidate_id": "RCAND-TWO",
                "candidate_title": "Trend neutral failure",
                "feature_name": "trend_state",
                "feature_family": "trend",
                "condition_value": "NEUTRAL",
                "candidate_score": 0.80,
            },
        ]),
        "program_dimensions": pd.DataFrame([
            {
                "research_program_id": "RPROG-ONE",
                "dimension": "volatility",
            },
            {
                "research_program_id": "RPROG-ONE",
                "dimension": "trend",
            },
        ]),
        "program_conflicts": pd.DataFrame(),
        "candidate_scores": pd.DataFrame([
            {
                "candidate_id": "RCAND-ONE",
                "final_priority_score": 0.81,
            },
            {
                "candidate_id": "RCAND-TWO",
                "final_priority_score": 0.80,
            },
        ]),
        "historical_validation": {},
        "compiler_report": {
            "state_hash": "a" * 64,
        },
    }


def test_experiment_ids_are_deterministic():
    first = experiment_id(
        program_id="RPROG-ONE",
        state_hash="a" * 64,
    )

    second = experiment_id(
        program_id="RPROG-ONE",
        state_hash="a" * 64,
    )

    assert first == second


def test_only_approved_unblocked_programs_are_designed():
    bundle = build_experiment_design_bundle(
        sources()
    )

    assert len(
        bundle["designs"]
    ) == 1

    assert (
        bundle[
            "designs"
        ].iloc[0][
            "research_program_id"
        ]
        == "RPROG-ONE"
    )


def test_design_contains_hypothesis_and_control():
    bundle = build_experiment_design_bundle(
        sources()
    )

    design = bundle[
        "designs"
    ].iloc[0]

    assert design["hypothesis"]
    assert design[
        "null_hypothesis"
    ]
    assert design[
        "baseline_definition"
    ]
    assert design[
        "candidate_definition"
    ]


def test_variants_preserve_candidate_lineage():
    bundle = build_experiment_design_bundle(
        sources()
    )

    assert set(
        bundle[
            "variants"
        ][
            "source_candidate_id"
        ]
    ) == {
        "RCAND-ONE",
        "RCAND-TWO",
    }


def test_walk_forward_plan_is_non_overlapping():
    bundle = build_experiment_design_bundle(
        sources()
    )

    folds = bundle["folds"]

    assert len(folds) == 6
    assert not folds[
        "uses_future_data"
    ].astype(bool).any()
    assert not folds[
        "overlapping_test_trades"
    ].astype(bool).any()


def test_acceptance_criteria_include_core_safety_rules():
    bundle = build_experiment_design_bundle(
        sources()
    )

    names = set(
        bundle[
            "criteria"
        ][
            "criterion_name"
        ]
    )

    assert "future_data_used" in names
    assert (
        "overlapping_test_trades"
        in names
    )
    assert "fold_win_rate" in names
    assert "retention_ratio" in names


def test_design_validation_passes():
    bundle = build_experiment_design_bundle(
        sources()
    )

    assert bundle[
        "validation"
    ][
        "passed"
    ].astype(bool).all()


def test_designer_never_authorizes_execution():
    bundle = build_experiment_design_bundle(
        sources()
    )

    assert not bundle[
        "designs"
    ][
        "execution_authorized"
    ].astype(bool).any()

    assert not bundle[
        "designs"
    ][
        "execution_instruction"
    ].astype(bool).any()

    assert not bundle[
        "designs"
    ][
        "production_eligible"
    ].astype(bool).any()
