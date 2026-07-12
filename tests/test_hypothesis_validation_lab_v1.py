"""Tests for Research Hypothesis Validation Lab v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.hypothesis_validation.decision import (
    build_validation_decision,
)
from atlas.investment.hypothesis_validation.states import (
    apply_state_definition,
    build_gate_mask,
    fit_state_definition,
)
from atlas.investment.hypothesis_validation.walk_forward import (
    validate_hypothesis,
)


def evidence() -> pd.DataFrame:
    rows = []

    for day in range(720):
        timestamp = (
            pd.Timestamp(
                "2024-01-01",
                tz="UTC",
            )
            + pd.Timedelta(
                days=day
            )
        )

        state_group = day % 3

        volatility = {
            0: 0.20,
            1: 0.50,
            2: 0.90,
        }[state_group]

        strategy_return = {
            0: -0.020,
            1: 0.005,
            2: 0.025,
        }[state_group]

        rows.append({
            "engine_id": "trend_test_v1",
            "family": "trend",
            "asset": "BTC-USD",
            "timestamp": timestamp,
            "strategy_return": (
                strategy_return
            ),
            "direction": "LONG",
            "regime": "TEST",
            "volatility_30d": (
                volatility
            ),
            "trend_state": (
                "UPTREND"
                if state_group == 2
                else "NEUTRAL"
            ),
        })

    return pd.DataFrame(rows)


def opportunity_hypothesis() -> dict:
    return {
        "hypothesis_id": "HYP-TEST-OPP",
        "hypothesis_type": (
            "CONDITIONAL_OPPORTUNITY"
        ),
        "engine_id": "trend_test_v1",
        "family": "trend",
        "feature": "volatility_30d",
        "state": "HIGH",
    }


def failure_hypothesis() -> dict:
    return {
        "hypothesis_id": "HYP-TEST-FAIL",
        "hypothesis_type": (
            "FAILURE_MODE_GATE"
        ),
        "engine_id": "trend_test_v1",
        "family": "trend",
        "feature": "volatility_30d",
        "state": "LOW",
    }


def test_numeric_thresholds_fit_training_only():
    training = evidence().iloc[:300]

    definition = fit_state_definition(
        training,
        feature="volatility_30d",
    )

    assert definition is not None

    assert (
        definition.feature_type
        == "NUMERIC_TERCILE"
    )


def test_failure_gate_excludes_target_state():
    frame = evidence().iloc[:12]

    definition = fit_state_definition(
        frame,
        feature="volatility_30d",
    )

    states = apply_state_definition(
        frame,
        definition,
    )

    mask = build_gate_mask(
        states,
        hypothesis_type=(
            "FAILURE_MODE_GATE"
        ),
        target_state="LOW",
    )

    assert not states[
        mask
    ].eq("LOW").any()


def test_conditional_gate_keeps_target_state():
    frame = evidence().iloc[:12]

    definition = fit_state_definition(
        frame,
        feature="volatility_30d",
    )

    states = apply_state_definition(
        frame,
        definition,
    )

    mask = build_gate_mask(
        states,
        hypothesis_type=(
            "CONDITIONAL_OPPORTUNITY"
        ),
        target_state="HIGH",
    )

    assert states[
        mask
    ].eq("HIGH").all()


def test_walk_forward_produces_folds():
    result = validate_hypothesis(
        opportunity_hypothesis(),
        evidence(),
    )

    assert not result[
        "folds"
    ].empty

    assert (
        result[
            "folds"
        ][
            "candidate_trade_count"
        ] > 0
    ).all()


def test_strong_opportunity_validates():
    result = validate_hypothesis(
        opportunity_hypothesis(),
        evidence(),
    )

    decision = build_validation_decision(
        opportunity_hypothesis(),
        result["folds"],
    )

    assert decision[
        "decision"
    ] == "VALIDATE"


def test_strong_failure_gate_validates():
    result = validate_hypothesis(
        failure_hypothesis(),
        evidence(),
    )

    decision = build_validation_decision(
        failure_hypothesis(),
        result["folds"],
    )

    assert decision[
        "decision"
    ] == "VALIDATE"


def test_empty_folds_return_insufficient_data():
    decision = build_validation_decision(
        opportunity_hypothesis(),
        pd.DataFrame(),
    )

    assert (
        decision["decision"]
        == "INSUFFICIENT_DATA"
    )


def test_decision_never_issues_execution():
    result = validate_hypothesis(
        opportunity_hypothesis(),
        evidence(),
    )

    decision = build_validation_decision(
        opportunity_hypothesis(),
        result["folds"],
    )

    assert (
        decision[
            "execution_instruction"
        ]
        is False
    )
