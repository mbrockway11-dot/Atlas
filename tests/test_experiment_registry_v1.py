"""Tests for Atlas Experiment Registry v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.experiment_registry.builder import (
    build_registry_bundle,
)
from atlas.investment.experiment_registry.identity import (
    build_experiment_id,
)
from atlas.investment.experiment_registry.storage import (
    merge_registry_bundle,
)


def sources() -> dict:
    return {
        "meta_hypotheses": pd.DataFrame([
            {
                "hypothesis_id": "HYP-ONE",
                "hypothesis": (
                    "Exclude low-volatility states."
                ),
                "engine_id": (
                    "trend_continuation_v1"
                ),
                "status": "PROPOSED",
            }
        ]),
        "hypothesis_validation": pd.DataFrame([
            {
                "hypothesis_id": "HYP-ONE",
                "validation_passed": True,
                "fold_win_rate": 0.83,
                "sharpe_advantage": 0.48,
            }
        ]),
        "validated_variants": pd.DataFrame([
            {
                "variant_id": "VAR-ONE",
                "variant_name": (
                    "trend_without_low_volatility"
                ),
                "hypothesis_id": "HYP-ONE",
                "parent_engine_id": (
                    "trend_continuation_v1"
                ),
                "gate_expression": (
                    "ALLOW_SIGNAL = volatility != LOW"
                ),
                "validation_score": 1.0,
            }
        ]),
        "variant_review": pd.DataFrame(),
        "variant_decisions": pd.DataFrame([
            {
                "variant_id": "VAR-ONE",
                "hypothesis_id": "HYP-ONE",
                "manual_decision": "APPROVED",
                "manual_reviewer": (
                    "Michael Elvis Brockway"
                ),
            }
        ]),
        "implementation_plans": pd.DataFrame(),
        "portfolio_promotion_v1": (
            pd.DataFrame()
        ),
        "portfolio_promotion_v2": (
            pd.DataFrame()
        ),
        "orchestrator_history": pd.DataFrame([
            {
                "run_id": "ORCH-ONE",
                "mode": "DRY_RUN",
                "success": True,
                "planned_jobs": 0,
            }
        ]),
        "orchestrator_report": {},
        "compiler_report": {
            "state_hash": "a" * 64,
        },
    }


def test_experiment_ids_are_deterministic():
    first = build_experiment_id(
        experiment_type="HYPOTHESIS",
        natural_key="HYP-ONE",
    )

    second = build_experiment_id(
        experiment_type="HYPOTHESIS",
        natural_key="HYP-ONE",
    )

    assert first == second


def test_registry_builds_hypothesis_variant_and_cycle():
    bundle = build_registry_bundle(
        sources()
    )

    types = set(
        bundle[
            "experiments"
        ][
            "experiment_type"
        ]
    )

    assert "HYPOTHESIS" in types
    assert "VALIDATED_VARIANT" in types
    assert "RESEARCH_CYCLE" in types


def test_variant_links_to_hypothesis():
    bundle = build_registry_bundle(
        sources()
    )

    assert (
        "GENERATED_VARIANT"
        in set(
            bundle[
                "relationships"
            ][
                "relationship_type"
            ]
        )
    )


def test_metrics_are_extracted():
    bundle = build_registry_bundle(
        sources()
    )

    names = set(
        bundle[
            "metrics"
        ][
            "metric_name"
        ]
    )

    assert "fold_win_rate" in names
    assert "sharpe_advantage" in names


def test_merge_is_append_only_and_idempotent():
    incoming = build_registry_bundle(
        sources()
    )

    empty = {
        key: pd.DataFrame()
        for key in incoming
    }

    first, first_stats = (
        merge_registry_bundle(
            existing=empty,
            incoming=incoming,
        )
    )

    second, second_stats = (
        merge_registry_bundle(
            existing=first,
            incoming=incoming,
        )
    )

    assert (
        len(
            first["experiments"]
        )
        == len(
            second["experiments"]
        )
    )

    assert (
        second_stats[
            "experiments"
        ][
            "inserted_rows"
        ]
        == 0
    )


def test_registry_never_marks_production_eligible():
    bundle = build_registry_bundle(
        sources()
    )

    assert not bundle[
        "experiments"
    ][
        "production_eligible"
    ].astype(bool).any()

    assert not bundle[
        "experiments"
    ][
        "execution_instruction"
    ].astype(bool).any()


def test_human_approval_is_preserved_as_observation():
    bundle = build_registry_bundle(
        sources()
    )

    matching = bundle[
        "observations"
    ][
        bundle[
            "observations"
        ][
            "source_name"
        ].eq(
            "variant_decisions"
        )
    ]

    assert not matching.empty

    assert (
        "APPROVED"
        in set(
            matching["status"]
        )
    )
