from __future__ import annotations

import pandas as pd

from atlas.investment.morphology_intelligence.execution_decision import (
    AVOID,
    ENTER,
    FLAT,
    LONG,
    MorphologyExecutionConfig,
    build_morphology_execution_decisions,
)


def _field() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "timestamp":
                "2026-01-01T00:00:00+00:00",
            "field_supported":
                True,
            "field_high_rotation":
                True,
            "field_high_expansion":
                False,
            "field_predictability":
                0.80,
            "field_divergence":
                0.40,
            "field_curl":
                1.20,
            "field_strain_magnitude":
                0.30,
            "field_flow_class":
                "ROTATING_CCW",
        }
    ])


def _evolution(
    signal: str = "STRONG_APPROACH",
) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "timestamp":
                "2026-01-01T00:00:00+00:00",
            "asset":
                asset,
            "evolution_signal":
                signal,
            "estimated_bars_to_attractor":
                12.0,
        }
        for asset in (
            "BTC",
            "ETH",
            "SOL",
        )
    ])


def _trajectory() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "window_end":
                "2026-01-01T00:00:00+00:00",
            "asset":
                asset,
            "recommended_action":
                "ENTER",
            "recommended_direction":
                "LONG",
            "trajectory_score":
                0.001,
            "observation_count":
                500,
        }
        for asset in (
            "BTC",
            "ETH",
            "SOL",
        )
    ])


def _discovery() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "asset":
                "SOL",
            "direction":
                "LONG",
            "expression":
                "field_high_rotation == True",
            "validated":
                True,
            "validation_fold_count":
                10,
            "validation_positive_uplift_rate":
                0.80,
            "validation_net_return":
                0.004,
            "validation_weighted_uplift":
                0.002,
            "validation_bh_adjusted_p_value":
                0.02,
        }
    ])


def test_validated_matching_condition_can_enter() -> None:
    decisions = (
        build_morphology_execution_decisions(
            latest_trajectories=(
                _trajectory()
            ),
            latest_evolution=(
                _evolution()
            ),
            latest_field=(
                _field()
            ),
            validated_discovery=(
                _discovery()
            ),
            config=(
                MorphologyExecutionConfig(
                    minimum_entry_confidence=0.55,
                )
            ),
        )
    )

    sol = decisions[
        decisions["asset"].eq("SOL")
    ].iloc[0]

    assert sol["action"] == ENTER
    assert sol["direction"] == LONG
    assert bool(
        sol["entry_ready"]
    )
    assert sol[
        "target_exposure"
    ] <= 0.10
    assert not bool(
        sol["live_authorized"]
    )


def test_missing_discovery_produces_no_entry() -> None:
    decisions = (
        build_morphology_execution_decisions(
            latest_trajectories=(
                _trajectory()
            ),
            latest_evolution=(
                _evolution()
            ),
            latest_field=(
                _field()
            ),
            validated_discovery=(
                pd.DataFrame()
            ),
        )
    )

    assert (
        decisions[
            "entry_ready"
        ].astype(bool).sum()
        == 0
    )

    assert set(
        decisions["direction"]
    ) == {
        FLAT,
    }


def test_receding_evolution_blocks_entry() -> None:
    decisions = (
        build_morphology_execution_decisions(
            latest_trajectories=(
                _trajectory()
            ),
            latest_evolution=(
                _evolution(
                    "RECEDING"
                )
            ),
            latest_field=(
                _field()
            ),
            validated_discovery=(
                _discovery()
            ),
            config=(
                MorphologyExecutionConfig(
                    minimum_entry_confidence=0.50,
                )
            ),
        )
    )

    sol = decisions[
        decisions["asset"].eq("SOL")
    ].iloc[0]

    assert not bool(
        sol["entry_ready"]
    )

    assert sol["action"] == AVOID

    assert (
        "receding_from_attractor"
        in sol["reasons"]
    )


def test_decisions_are_deterministic() -> None:
    first = (
        build_morphology_execution_decisions(
            latest_trajectories=_trajectory(),
            latest_evolution=_evolution(),
            latest_field=_field(),
            validated_discovery=_discovery(),
        )
    )

    second = (
        build_morphology_execution_decisions(
            latest_trajectories=_trajectory(),
            latest_evolution=_evolution(),
            latest_field=_field(),
            validated_discovery=_discovery(),
        )
    )

    assert (
        first[
            "decision_id"
        ].tolist()
        == second[
            "decision_id"
        ].tolist()
    )


def test_engine_never_authorizes_live_trading() -> None:
    decisions = (
        build_morphology_execution_decisions(
            latest_trajectories=_trajectory(),
            latest_evolution=_evolution(),
            latest_field=_field(),
            validated_discovery=_discovery(),
        )
    )

    assert not decisions[
        "live_authorized"
    ].astype(bool).any()
