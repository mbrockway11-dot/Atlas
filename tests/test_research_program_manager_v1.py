"""Tests for Atlas Research Program Manager v1."""

from __future__ import annotations

import pandas as pd
import pytest

from atlas.investment.research_program_manager.evaluation import (
    build_program_dependencies,
    build_program_queues,
    evaluate_program_state,
)
from atlas.investment.research_program_manager.identity import (
    normalize_status,
    validate_transition,
)
from atlas.investment.research_program_manager.registry import (
    build_program_evidence,
    build_program_registry,
)
from atlas.investment.research_program_manager.transitions import (
    record_program_transition,
)


def consolidated_programs() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "program_rank": 1,
            "research_program_id": (
                "RPROG-ONE"
            ),
            "program_title": (
                "Momentum degradation program"
            ),
            "program_theme": (
                "momentum|volatility|degradation"
            ),
            "parent_engine_id": (
                "cross_sectional_momentum_v1"
            ),
            "engine_family": "momentum",
            "member_count": 8,
            "dimension_count": 3,
            "condition_count": 6,
            "mean_candidate_score": 0.78,
            "max_candidate_score": 0.82,
            "program_priority_score": 0.81,
            "cluster_confidence": 0.76,
            "priority_band": "CRITICAL",
            "recommendation": (
                "RESEARCH_NOW"
            ),
            "has_conflicts": False,
        },
        {
            "program_rank": 2,
            "research_program_id": (
                "RPROG-TWO"
            ),
            "program_title": (
                "Unresolved general program"
            ),
            "program_theme": (
                "general|other"
            ),
            "parent_engine_id": "",
            "engine_family": "",
            "member_count": 3,
            "dimension_count": 1,
            "condition_count": 2,
            "mean_candidate_score": 0.60,
            "max_candidate_score": 0.65,
            "program_priority_score": 0.62,
            "cluster_confidence": 0.55,
            "priority_band": "MEDIUM",
            "recommendation": "QUEUE",
            "has_conflicts": True,
        },
    ])


def members() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "research_program_id": (
                "RPROG-ONE"
            ),
            "candidate_id": (
                "RCAND-ONE"
            ),
            "candidate_title": (
                "Momentum ATR failure"
            ),
            "candidate_score": 0.82,
        },
        {
            "research_program_id": (
                "RPROG-ONE"
            ),
            "candidate_id": (
                "RCAND-TWO"
            ),
            "candidate_title": (
                "Momentum liquidity failure"
            ),
            "candidate_score": 0.80,
        },
    ])


def dimensions() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "research_program_id": (
                "RPROG-ONE"
            ),
            "dimension": "volatility",
        },
        {
            "research_program_id": (
                "RPROG-ONE"
            ),
            "dimension": "liquidity",
        },
    ])


def conflicts() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "research_program_id": (
                "RPROG-TWO"
            ),
            "feature_name": "regime",
            "conflict_type": (
                "MULTIPLE_FAILURE_CONDITIONS"
            ),
        }
    ])


def test_status_normalization():
    assert (
        normalize_status(
            "approved"
        )
        == "APPROVED_FOR_DESIGN"
    )


def test_legal_transition_passes():
    validate_transition(
        "PROPOSED",
        "APPROVED_FOR_DESIGN",
    )


def test_illegal_transition_fails():
    with pytest.raises(
        ValueError
    ):
        validate_transition(
            "PROPOSED",
            "PROMOTED",
        )


def test_registry_starts_programs_as_proposed():
    registry = build_program_registry(
        consolidated_programs=(
            consolidated_programs()
        ),
        existing_registry=(
            pd.DataFrame()
        ),
        state_hash="a" * 64,
    )

    assert set(
        registry[
            "current_status"
        ]
    ) == {
        "PROPOSED"
    }


def test_registry_preserves_existing_decision():
    existing = pd.DataFrame([
        {
            "research_program_id": (
                "RPROG-ONE"
            ),
            "current_status": (
                "APPROVED_FOR_DESIGN"
            ),
            "reviewer": "Michael",
            "decision_rationale": (
                "Approved."
            ),
            "status_locked": True,
        }
    ])

    registry = build_program_registry(
        consolidated_programs=(
            consolidated_programs()
        ),
        existing_registry=existing,
        state_hash="a" * 64,
    )

    matching = registry[
        registry[
            "research_program_id"
        ].eq("RPROG-ONE")
    ].iloc[0]

    assert (
        matching[
            "current_status"
        ]
        == "APPROVED_FOR_DESIGN"
    )

    assert (
        matching["reviewer"]
        == "Michael"
    )


def test_program_evidence_preserves_candidate_lineage():
    registry = build_program_registry(
        consolidated_programs=(
            consolidated_programs()
        ),
        existing_registry=(
            pd.DataFrame()
        ),
        state_hash="a" * 64,
    )

    evidence = build_program_evidence(
        registry=registry,
        members=members(),
        dimensions=dimensions(),
        conflicts=conflicts(),
        state_hash="a" * 64,
    )

    assert (
        "RCAND-ONE"
        in set(
            evidence[
                "source_record_key"
            ]
        )
    )


def test_missing_engine_is_blocking():
    registry = build_program_registry(
        consolidated_programs=(
            consolidated_programs()
        ),
        existing_registry=(
            pd.DataFrame()
        ),
        state_hash="a" * 64,
    )

    dependencies = (
        build_program_dependencies(
            registry=registry,
            members=members(),
            conflicts=conflicts(),
        )
    )

    matching = dependencies[
        dependencies[
            "research_program_id"
        ].eq("RPROG-TWO")
    ]

    assert matching[
        "blocking"
    ].astype(bool).any()


def test_state_evaluation_marks_blocked_program():
    registry = build_program_registry(
        consolidated_programs=(
            consolidated_programs()
        ),
        existing_registry=(
            pd.DataFrame()
        ),
        state_hash="a" * 64,
    )

    evidence = build_program_evidence(
        registry=registry,
        members=members(),
        dimensions=dimensions(),
        conflicts=conflicts(),
        state_hash="a" * 64,
    )

    dependencies = (
        build_program_dependencies(
            registry=registry,
            members=members(),
            conflicts=conflicts(),
        )
    )

    evaluated = evaluate_program_state(
        registry=registry,
        evidence=evidence,
        dependencies=dependencies,
    )

    matching = evaluated[
        evaluated[
            "research_program_id"
        ].eq("RPROG-TWO")
    ].iloc[0]

    assert bool(
        matching["is_blocked"]
    )


def test_manual_transition_is_recorded():
    registry = build_program_registry(
        consolidated_programs=(
            consolidated_programs()
        ),
        existing_registry=(
            pd.DataFrame()
        ),
        state_hash="a" * 64,
    )

    (
        updated,
        history,
        history_row,
    ) = record_program_transition(
        registry=registry,
        history=pd.DataFrame(),
        program_id="RPROG-ONE",
        new_status=(
            "APPROVED_FOR_DESIGN"
        ),
        reviewer=(
            "Michael Elvis Brockway"
        ),
        rationale=(
            "Approved for experiment design."
        ),
    )

    matching = updated[
        updated[
            "research_program_id"
        ].eq("RPROG-ONE")
    ].iloc[0]

    assert (
        matching[
            "current_status"
        ]
        == "APPROVED_FOR_DESIGN"
    )

    assert len(history) == 1

    assert (
        history_row[
            "new_status"
        ]
        == "APPROVED_FOR_DESIGN"
    )


def test_queues_are_created():
    registry = build_program_registry(
        consolidated_programs=(
            consolidated_programs()
        ),
        existing_registry=(
            pd.DataFrame()
        ),
        state_hash="a" * 64,
    )

    queues = build_program_queues(
        registry
    )

    assert len(
        queues["approval"]
    ) == 2


def test_manager_never_authorizes_execution():
    registry = build_program_registry(
        consolidated_programs=(
            consolidated_programs()
        ),
        existing_registry=(
            pd.DataFrame()
        ),
        state_hash="a" * 64,
    )

    assert not registry[
        "implementation_authorized"
    ].astype(bool).any()

    assert not registry[
        "production_eligible"
    ].astype(bool).any()

    assert not registry[
        "execution_instruction"
    ].astype(bool).any()
