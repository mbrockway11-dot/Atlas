"""Tests for Adaptive Research Prioritizer v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.adaptive_research_prioritizer.candidates import (
    build_research_candidates,
)
from atlas.investment.adaptive_research_prioritizer.queue import (
    build_explanations,
    build_priority_queue,
)
from atlas.investment.adaptive_research_prioritizer.scoring import (
    score_research_candidates,
)


def sources() -> dict:
    return {
        "research_priorities": pd.DataFrame([
            {
                "priority_id": "PRI-ONE",
                "title": (
                    "Investigate momentum transition failures"
                ),
                "engine_id": "momentum_v1",
                "engine_family": "momentum",
                "failure_mode": (
                    "transition_whipsaw"
                ),
                "priority_score": 0.90,
                "description": (
                    "Momentum degrades during transition states."
                ),
            }
        ]),
        "hypothesis_library": pd.DataFrame([
            {
                "hypothesis_id": "HYP-ONE",
                "hypothesis": (
                    "Gate momentum during transition."
                ),
                "engine_id": "momentum_v1",
                "engine_family": "momentum",
                "failure_mode": (
                    "transition_whipsaw"
                ),
                "proposed_gate": (
                    "ALLOW_SIGNAL = regime != TRANSITION"
                ),
                "priority_score": 0.85,
            }
        ]),
        "failure_modes": pd.DataFrame([
            {
                "engine_id": "momentum_v1",
                "engine_family": "momentum",
                "failure_mode": (
                    "transition_whipsaw"
                ),
                "recommended_gate": (
                    "ALLOW_SIGNAL = regime != TRANSITION"
                ),
            },
            {
                "engine_id": "momentum_v1",
                "engine_family": "momentum",
                "failure_mode": (
                    "transition_whipsaw"
                ),
            },
        ]),
        "family_gaps": pd.DataFrame([
            {
                "engine_family": (
                    "liquidity"
                ),
                "gap_score": 0.80,
                "recommended_research": (
                    "Build liquidity stress prototype."
                ),
            }
        ]),
        "feature_interactions": pd.DataFrame(),
        "experiment_registry": pd.DataFrame([
            {
                "experiment_id": "EXP-OLD",
                "title": (
                    "Unrelated volatility hypothesis"
                ),
                "description": (
                    "Test volatility expansion."
                ),
                "hypothesis_id": (
                    "HYP-OTHER"
                ),
                "current_status": (
                    "REJECTED"
                ),
            }
        ]),
        "experiment_observations": (
            pd.DataFrame()
        ),
        "experiment_metrics": (
            pd.DataFrame()
        ),
        "graph_nodes": pd.DataFrame([
            {
                "node_id": "NODE-ENGINE",
                "natural_key": (
                    "momentum_v1"
                ),
                "engine_id": (
                    "momentum_v1"
                ),
                "hypothesis_id": "",
            }
        ]),
        "graph_edges": pd.DataFrame(),
        "graph_metrics": pd.DataFrame([
            {
                "node_id": "NODE-ENGINE",
                "total_degree": 5,
            }
        ]),
        "validated_variants": (
            pd.DataFrame()
        ),
        "variant_decisions": (
            pd.DataFrame()
        ),
        "implementation_queue": (
            pd.DataFrame()
        ),
        "scheduler": pd.DataFrame(),
        "regime_report": {
            "regime": {
                "regime": "TRANSITION",
                "primary_regime": (
                    "MEAN_REVERTING_DISPERSION"
                ),
                "secondary_regime": (
                    "SELECTIVE_TRENDING_RISK_ON"
                ),
                "is_transition": True,
            }
        },
        "fusion_report": {},
        "compiler_report": {
            "state_hash": "a" * 64,
        },
    }


def test_candidates_are_built():
    candidates = (
        build_research_candidates(
            sources()
        )
    )

    assert not candidates.empty

    assert {
        "RESEARCH_PRIORITY",
        "HYPOTHESIS",
        "FAILURE_MODE_GATE",
        "ENGINE_FAMILY_GAP",
    }.issubset(
        set(
            candidates[
                "candidate_type"
            ]
        )
    )


def test_scoring_produces_normalized_scores():
    candidates = (
        build_research_candidates(
            sources()
        )
    )

    result = score_research_candidates(
        candidates,
        sources(),
    )

    scores = result["scores"]

    assert (
        scores[
            "final_priority_score"
        ].between(
            0.0,
            1.0,
        ).all()
    )


def test_transition_failure_scores_regime_relevance():
    candidates = (
        build_research_candidates(
            sources()
        )
    )

    result = score_research_candidates(
        candidates,
        sources(),
    )

    matching = result[
        "scores"
    ][
        result[
            "scores"
        ][
            "failure_recurrence_score"
        ].gt(0.5)
    ]

    assert not matching.empty

    assert matching[
        "regime_relevance_score"
    ].max() >= 0.75


def test_priority_queue_is_ranked():
    candidates = (
        build_research_candidates(
            sources()
        )
    )

    result = score_research_candidates(
        candidates,
        sources(),
    )

    queue = build_priority_queue(
        result["scores"]
    )

    assert queue[
        "priority_rank"
    ].tolist() == list(
        range(
            1,
            len(queue) + 1,
        )
    )

    assert queue[
        "final_priority_score"
    ].is_monotonic_decreasing


def test_queue_never_authorizes_execution():
    candidates = (
        build_research_candidates(
            sources()
        )
    )

    result = score_research_candidates(
        candidates,
        sources(),
    )

    queue = build_priority_queue(
        result["scores"]
    )

    assert not queue[
        "execution_authorized"
    ].astype(bool).any()

    assert not queue[
        "execution_instruction"
    ].astype(bool).any()

    assert queue[
        "approval_required"
    ].astype(bool).all()


def test_explanations_are_created():
    candidates = (
        build_research_candidates(
            sources()
        )
    )

    result = score_research_candidates(
        candidates,
        sources(),
    )

    explanations = (
        build_explanations(
            result["scores"]
        )
    )

    assert len(
        explanations
    ) == len(
        result["scores"]
    )

    assert explanations[
        "explanation"
    ].str.len().gt(20).all()


def test_duplicate_candidate_is_penalized():
    modified = sources()

    modified[
        "experiment_registry"
    ] = pd.DataFrame([
        {
            "experiment_id": "EXP-HYP",
            "title": (
                "Gate momentum during transition"
            ),
            "description": (
                "ALLOW_SIGNAL = regime != TRANSITION"
            ),
            "hypothesis_id": "HYP-ONE",
            "current_status": (
                "VALIDATED"
            ),
        }
    ])

    candidates = (
        build_research_candidates(
            modified
        )
    )

    result = score_research_candidates(
        candidates,
        modified,
    )

    matching = result[
        "scores"
    ][
        result[
            "scores"
        ][
            "natural_key"
        ].eq("HYP-ONE")
    ]

    assert not matching.empty

    assert float(
        matching.iloc[0][
            "duplication_penalty"
        ]
    ) > 0

    assert not bool(
        matching.iloc[0][
            "rank_eligible"
        ]
    )
