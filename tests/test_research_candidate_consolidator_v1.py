"""Tests for Atlas Research Candidate Consolidator v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.research_candidate_consolidator.clustering import (
    build_candidate_clusters,
    candidate_similarity,
)
from atlas.investment.research_candidate_consolidator.enrichment import (
    enrich_candidates,
)
from atlas.investment.research_candidate_consolidator.identity import (
    extract_condition_value,
    extract_feature_name,
    feature_family,
    program_id,
)
from atlas.investment.research_candidate_consolidator.programs import (
    build_research_programs,
)


def priority_queue() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "candidate_id": "RCAND-1",
            "candidate_type": (
                "FAILURE_MODE_GATE"
            ),
            "title": (
                "Investigate cross_sectional_momentum_v1 "
                "underperforms when atr_pct_14d is MID."
            ),
            "parent_engine_id": (
                "cross_sectional_momentum_v1"
            ),
            "engine_family": "momentum",
            "final_priority_score": 0.82,
            "priority_band": "CRITICAL",
            "recommendation": (
                "RESEARCH_NOW"
            ),
            "rank_eligible": True,
        },
        {
            "candidate_id": "RCAND-2",
            "candidate_type": (
                "FAILURE_MODE_GATE"
            ),
            "title": (
                "Investigate cross_sectional_momentum_v1 "
                "underperforms when atr_pct_14d is LOW."
            ),
            "parent_engine_id": (
                "cross_sectional_momentum_v1"
            ),
            "engine_family": "momentum",
            "final_priority_score": 0.81,
            "priority_band": "CRITICAL",
            "recommendation": (
                "RESEARCH_NOW"
            ),
            "rank_eligible": True,
        },
        {
            "candidate_id": "RCAND-3",
            "candidate_type": (
                "FAILURE_MODE_GATE"
            ),
            "title": (
                "Investigate cross_sectional_momentum_v1 "
                "underperforms when liquidity_state "
                "is CONTRACTING."
            ),
            "parent_engine_id": (
                "cross_sectional_momentum_v1"
            ),
            "engine_family": "momentum",
            "final_priority_score": 0.80,
            "priority_band": "CRITICAL",
            "recommendation": (
                "RESEARCH_NOW"
            ),
            "rank_eligible": True,
        },
        {
            "candidate_id": "RCAND-4",
            "candidate_type": (
                "FAILURE_MODE_GATE"
            ),
            "title": (
                "Investigate volatility_compression_v1 "
                "underperforms when trend_state is DOWNTREND."
            ),
            "parent_engine_id": (
                "volatility_compression_v1"
            ),
            "engine_family": "volatility",
            "final_priority_score": 0.70,
            "priority_band": "HIGH",
            "recommendation": "QUEUE",
            "rank_eligible": True,
        },
        {
            "candidate_id": "RCAND-5",
            "candidate_type": (
                "HYPOTHESIS"
            ),
            "title": "Already validated duplicate",
            "parent_engine_id": (
                "cross_sectional_momentum_v1"
            ),
            "engine_family": "momentum",
            "final_priority_score": 0.75,
            "priority_band": "HIGH",
            "recommendation": "QUEUE",
            "rank_eligible": False,
        },
    ])


def test_feature_extraction():
    title = (
        "Investigate engine underperforms when "
        "atr_pct_14d is MID."
    )

    assert (
        extract_feature_name(title)
        == "atr_pct_14d"
    )

    assert (
        extract_condition_value(title)
        == "MID"
    )

    assert (
        feature_family(
            "atr_pct_14d",
            title,
        )
        == "volatility"
    )


def test_program_ids_are_deterministic():
    first = program_id(
        engine_id="engine",
        theme="theme",
        member_ids=[
            "B",
            "A",
        ],
    )

    second = program_id(
        engine_id="engine",
        theme="theme",
        member_ids=[
            "A",
            "B",
        ],
    )

    assert first == second


def test_enrichment_adds_dimensions():
    enriched = enrich_candidates(
        priority_queue()
    )

    matching = enriched[
        enriched[
            "candidate_id"
        ].eq("RCAND-1")
    ].iloc[0]

    assert (
        matching[
            "feature_family"
        ]
        == "volatility"
    )

    assert (
        matching[
            "condition_value"
        ]
        == "MID"
    )


def test_same_engine_candidates_are_similar():
    enriched = enrich_candidates(
        priority_queue()
    )

    left = enriched.iloc[0].to_dict()
    right = enriched.iloc[1].to_dict()

    assert (
        candidate_similarity(
            left,
            right,
        )
        >= 0.42
    )


def test_different_engine_candidates_do_not_cluster():
    enriched = enrich_candidates(
        priority_queue()
    )

    left = enriched.iloc[0].to_dict()
    right = enriched.iloc[3].to_dict()

    assert (
        candidate_similarity(
            left,
            right,
        )
        == 0.0
    )


def test_clusters_exclude_rank_ineligible_candidates():
    enriched = enrich_candidates(
        priority_queue()
    )

    clusters = build_candidate_clusters(
        enriched
    )

    flattened = {
        candidate_id
        for cluster in clusters
        for candidate_id in cluster
    }

    assert "RCAND-5" not in flattened


def test_programs_preserve_member_lineage():
    enriched = enrich_candidates(
        priority_queue()
    )

    clusters = build_candidate_clusters(
        enriched
    )

    bundle = build_research_programs(
        enriched,
        clusters,
    )

    assert not bundle[
        "programs"
    ].empty

    assert not bundle[
        "members"
    ].empty

    assert set(
        bundle[
            "members"
        ][
            "candidate_id"
        ]
    ).issubset(
        set(
            enriched[
                "candidate_id"
            ]
        )
    )


def test_conflicting_conditions_are_detected():
    enriched = enrich_candidates(
        priority_queue()
    )

    clusters = build_candidate_clusters(
        enriched
    )

    bundle = build_research_programs(
        enriched,
        clusters,
    )

    conflicts = bundle[
        "conflicts"
    ]

    assert not conflicts.empty

    assert (
        "atr_pct_14d"
        in set(
            conflicts[
                "feature_name"
            ]
        )
    )


def test_programs_never_authorize_execution():
    enriched = enrich_candidates(
        priority_queue()
    )

    clusters = build_candidate_clusters(
        enriched
    )

    bundle = build_research_programs(
        enriched,
        clusters,
    )

    programs = bundle[
        "programs"
    ]

    assert not programs[
        "execution_authorized"
    ].astype(bool).any()

    assert not programs[
        "execution_instruction"
    ].astype(bool).any()

    assert programs[
        "approval_required"
    ].astype(bool).all()
