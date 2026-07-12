"""Tests for Atlas Research Experiment Execution Lab v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.research_experiment_execution.acceptance import (
    evaluate_acceptance_criteria,
)
from atlas.investment.research_experiment_execution.executor import (
    execute_experiment_bundle,
)
from atlas.investment.research_experiment_execution.folds import (
    assign_walk_forward_folds,
)
from atlas.investment.research_experiment_execution.gates import (
    apply_frozen_gate,
    parse_gate_expression,
)


def observations() -> pd.DataFrame:
    dates = pd.date_range(
        "2020-01-01",
        periods=120,
        freq="D",
        tz="UTC",
    )

    rows = []

    for index, timestamp in enumerate(
        dates
    ):
        rows.append({
            "trade_id": (
                f"TRADE-{index:03d}"
            ),
            "engine_id": (
                "trend_continuation_v1"
            ),
            "timestamp": timestamp,
            "trade_return": (
                -0.02
                if index % 5 == 0
                else 0.01
            ),
            "atr_pct_14d": (
                "MID"
                if index % 5 == 0
                else "HIGH"
            ),
        })

    return pd.DataFrame(rows)


def sources() -> dict:
    experiment_id = "REXP-ONE"

    return {
        "program_registry": pd.DataFrame([
            {
                "research_program_id": (
                    "RPROG-ONE"
                ),
                "current_status": (
                    "EXPERIMENT_DESIGNED"
                ),
                "is_blocked": False,
            }
        ]),
        "designs": pd.DataFrame([
            {
                "experiment_id": (
                    experiment_id
                ),
                "research_program_id": (
                    "RPROG-ONE"
                ),
                "parent_engine_id": (
                    "trend_continuation_v1"
                ),
                "fold_count": 6,
                "embargo_days": 7,
            }
        ]),
        "variants": pd.DataFrame([
            {
                "experiment_variant_id": (
                    "REXVAR-ONE"
                ),
                "experiment_id": (
                    experiment_id
                ),
                "research_program_id": (
                    "RPROG-ONE"
                ),
                "source_candidate_id": (
                    "RCAND-ONE"
                ),
                "gate_expression": (
                    "ALLOW_SIGNAL = NOT "
                    "(atr_pct_14d == 'MID')"
                ),
            }
        ]),
        "fold_plan": pd.DataFrame(),
        "acceptance_criteria": pd.DataFrame([
            {
                "criterion_id": "CRIT-1",
                "experiment_id": (
                    experiment_id
                ),
                "criterion_name": (
                    "minimum_candidate_trades"
                ),
                "operator": ">=",
                "threshold_value": 30,
                "failure_action": (
                    "DO_NOT_PROMOTE"
                ),
            },
            {
                "criterion_id": "CRIT-2",
                "experiment_id": (
                    experiment_id
                ),
                "criterion_name": (
                    "mean_return_advantage"
                ),
                "operator": ">",
                "threshold_value": 0.0,
                "failure_action": (
                    "DO_NOT_PROMOTE"
                ),
            },
            {
                "criterion_id": "CRIT-3",
                "experiment_id": (
                    experiment_id
                ),
                "criterion_name": (
                    "future_data_used"
                ),
                "operator": "==",
                "threshold_value": False,
                "failure_action": (
                    "DO_NOT_PROMOTE"
                ),
            },
            {
                "criterion_id": "CRIT-4",
                "experiment_id": (
                    experiment_id
                ),
                "criterion_name": (
                    "overlapping_test_trades"
                ),
                "operator": "==",
                "threshold_value": False,
                "failure_action": (
                    "DO_NOT_PROMOTE"
                ),
            },
        ]),
        "design_validation": pd.DataFrame([
            {
                "experiment_id": (
                    experiment_id
                ),
                "check_id": check_id,
                "passed": True,
            }
            for check_id in (
                "PROGRAM_STATUS_ELIGIBLE",
                "PROGRAM_NOT_BLOCKED",
                "PARENT_ENGINE_PRESENT",
                "PROGRAM_MEMBERS_PRESENT",
                "PROGRAM_DIMENSIONS_PRESENT",
                "NO_UNRESOLVED_CONFLICTS",
            )
        ]),
        "observations": observations(),
        "observation_source_path": (
            "test_observations.csv"
        ),
        "compiler_report": {
            "state_hash": "a" * 64,
        },
    }


def test_safe_gate_parser_accepts_frozen_equality_exclusion():
    parsed = parse_gate_expression(
        "ALLOW_SIGNAL = NOT "
        "(atr_pct_14d == 'MID')"
    )

    assert parsed["supported"]
    assert (
        parsed["feature_name"]
        == "atr_pct_14d"
    )
    assert (
        parsed["condition_value"]
        == "MID"
    )


def test_unsupported_gate_is_rejected():
    parsed = parse_gate_expression(
        "ALLOW_SIGNAL = custom_python()"
    )

    assert not parsed["supported"]


def test_gate_excludes_declared_condition():
    frame = observations()

    allowed, parsed = apply_frozen_gate(
        frame,
        "ALLOW_SIGNAL = NOT "
        "(atr_pct_14d == 'MID')",
    )

    assert parsed["supported"]

    retained = frame[
        allowed
    ]

    assert not retained[
        "atr_pct_14d"
    ].eq("MID").any()


def test_walk_forward_folds_are_non_overlapping():
    assigned, plan = (
        assign_walk_forward_folds(
            observations(),
            fold_count=6,
            embargo_days=7,
        )
    )

    assert len(plan) == 6
    assert not plan[
        "overlap_detected"
    ].astype(bool).any()
    assert not plan[
        "uses_future_data"
    ].astype(bool).any()

    counts = assigned.groupby(
        "trade_id"
    ).size()

    assert counts.max() == 1


def test_acceptance_criteria_use_frozen_thresholds():
    criteria = sources()[
        "acceptance_criteria"
    ]

    results = (
        evaluate_acceptance_criteria(
            experiment_id="REXP-ONE",
            criteria=criteria,
            evidence={
                "minimum_candidate_trades": 90,
                "mean_return_advantage": 0.01,
                "future_data_used": False,
                "overlapping_test_trades": False,
            },
        )
    )

    assert results[
        "passed"
    ].astype(bool).all()


def test_execution_completes_designed_program():
    bundle = execute_experiment_bundle(
        sources()
    )

    assert len(
        bundle["runs"]
    ) == 1

    assert (
        bundle[
            "runs"
        ].iloc[0][
            "run_status"
        ]
        == "COMPLETED"
    )

    assert len(
        bundle[
            "variant_results"
        ]
    ) == 1


def test_candidate_improves_mean_return():
    bundle = execute_experiment_bundle(
        sources()
    )

    result = bundle[
        "variant_results"
    ].iloc[0]

    assert (
        float(
            result[
                "mean_return_advantage"
            ]
        )
        > 0
    )


def test_execution_preserves_trade_lineage():
    bundle = execute_experiment_bundle(
        sources()
    )

    comparison = bundle[
        "trade_comparison"
    ]

    assert not comparison.empty

    assert set(
        comparison[
            "trade_id"
        ]
    ).issubset(
        set(
            observations()[
                "trade_id"
            ]
        )
    )


def test_lab_never_authorizes_implementation():
    bundle = execute_experiment_bundle(
        sources()
    )

    assert not bundle[
        "runs"
    ][
        "implementation_authorized"
    ].astype(bool).any()

    assert not bundle[
        "runs"
    ][
        "production_eligible"
    ].astype(bool).any()

    assert not bundle[
        "variant_results"
    ][
        "implementation_authorized"
    ].astype(bool).any()

    assert not bundle[
        "variant_results"
    ][
        "production_eligible"
    ].astype(bool).any()
