"""Tests for Evidence Accumulator variant integration."""

from __future__ import annotations

import pandas as pd

from atlas.investment.validated_variants.research_evidence_bridge import (
    build_accumulated_evidence_variants,
)
from atlas.investment.variant_review.evidence import (
    build_longitudinal_map,
)


def durable_evidence() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "research_program_id": "RPROG-1",
            "experiment_id": "REXP-1",
            "experiment_variant_id": "REXVAR-1",
            "source_candidate_id": "RCAND-1",
            "run_count": 2,
            "run_pass_rate": 1.0,
            "baseline_trade_count": 200,
            "candidate_trade_count": 140,
            "mean_retention_ratio": 0.70,
            "mean_return_advantage": 0.02,
            "mean_sharpe_advantage": 0.30,
            "mean_drawdown_improvement": 0.10,
            "mean_fold_win_rate": 0.75,
            "consistency_score": 0.90,
            "contradiction_rate": 0.0,
            "decay_rate": 0.0,
            "sufficiency_score": 1.0,
            "evidence_score": 0.88,
            "durability_status": "DURABLE",
            "evidence_sufficient": True,
            "total_fold_count": 12,
            "distinct_state_hashes": 2,
        }
    ])


def recommendations() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "research_program_id": "RPROG-1",
            "experiment_id": "REXP-1",
            "recommendation": (
                "RECOMMEND_EVIDENCE_ACCUMULATING"
            ),
            "recommendation_reason": (
                "Durable accumulated evidence."
            ),
        }
    ])


def experiment_variants() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "experiment_variant_id": "REXVAR-1",
            "experiment_id": "REXP-1",
            "source_candidate_id": "RCAND-1",
            "feature_name": "trend_state",
            "condition_value": "NEUTRAL",
            "gate_expression": (
                "ALLOW_SIGNAL = NOT "
                "(trend_state == 'NEUTRAL')"
            ),
        }
    ])


def designs() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "experiment_id": "REXP-1",
            "research_program_id": "RPROG-1",
            "parent_engine_id": (
                "trend_continuation_v1"
            ),
            "engine_family": "trend",
            "hypothesis": (
                "Exclude neutral trend states."
            ),
            "null_hypothesis": (
                "No improvement."
            ),
        }
    ])


def test_durable_evidence_builds_registry_variant():
    result = build_accumulated_evidence_variants(
        accumulated_evidence=durable_evidence(),
        program_recommendations=recommendations(),
        experiment_variants=experiment_variants(),
        experiment_designs=designs(),
    )

    assert len(result) == 1
    assert result.iloc[0][
        "parent_engine_id"
    ] == "trend_continuation_v1"
    assert result.iloc[0][
        "feature"
    ] == "trend_state"
    assert result.iloc[0][
        "target_state"
    ] == "NEUTRAL"
    assert result.iloc[0][
        "source"
    ] == "research_evidence_accumulator_v1"
    assert not bool(
        result.iloc[0][
            "execution_instruction"
        ]
    )


def test_insufficient_evidence_does_not_register():
    evidence = durable_evidence()
    evidence.loc[
        0,
        "durability_status",
    ] = "INSUFFICIENT"

    result = build_accumulated_evidence_variants(
        accumulated_evidence=evidence,
        program_recommendations=recommendations(),
        experiment_variants=experiment_variants(),
        experiment_designs=designs(),
    )

    assert result.empty


def test_longitudinal_map_preserves_safety_metrics():
    frame = durable_evidence().copy()
    frame["variant_id"] = "VAR-ONE"

    result = build_longitudinal_map(
        frame
    )

    assert result["VAR-ONE"][
        "longitudinal_durability"
    ] == "DURABLE"

    assert result["VAR-ONE"][
        "longitudinal_evidence_sufficient"
    ]


def test_longitudinal_evidence_maps_to_canonical_variant_id():
    from atlas.investment.validated_variants.builder import (
        build_variant_id,
    )
    from atlas.investment.variant_review.loader import (
        enrich_longitudinal_evidence,
    )

    accumulated = durable_evidence()

    enriched = enrich_longitudinal_evidence(
        accumulated_evidence=accumulated,
        experiment_variants=experiment_variants(),
        experiment_designs=designs(),
    )

    expected = build_variant_id(
        parent_engine_id=(
            "trend_continuation_v1"
        ),
        hypothesis_type=(
            "FAILURE_MODE_GATE"
        ),
        feature="trend_state",
        state="NEUTRAL",
    )

    assert len(enriched) == 1

    assert (
        enriched.iloc[0][
            "variant_id"
        ]
        == expected
    )
