from __future__ import annotations

import pandas as pd

from atlas.investment.morphology_intelligence.historical_replay import (
    ADVERSE,
    NEUTRAL,
    SUPPORTIVE,
    MorphologyHistoricalReplayConfig,
    assemble_historical_morphology_state,
    build_morphology_historical_replay,
    score_historical_state,
)


def _calendar() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T01:00:00Z"
                ),
            "asset":
                "SOL",
            "calendar_action":
                "ENTER_LONG",
            "calendar_direction":
                "LONG",
        }
    ])


def _field(
    *,
    supported: bool = True,
    predictability: float = 0.80,
) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T00:45:00Z"
                ),
            "morphology_cluster_id":
                3,
            "field_supported":
                supported,
            "field_predictability":
                predictability,
            "field_flow_class":
                "ROTATING_CCW",
            "field_strain_magnitude":
                0.40,
        }
    ])


def _evolution(
    signal: str = "APPROACH",
) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T00:45:00Z"
                ),
            "asset":
                "SOL",
            "evolution_signal":
                signal,
            "estimated_bars_to_attractor":
                12.0,
        }
    ])


def _trajectory(
    action: str = "ENTER",
) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T00:45:00Z"
                ),
            "asset":
                "SOL",
            "recommended_action":
                action,
            "recommended_direction":
                "LONG",
            "trajectory_score":
                0.001,
            "observation_count":
                500,
        }
    ])


def _config() -> MorphologyHistoricalReplayConfig:
    return MorphologyHistoricalReplayConfig(
        supportive_confidence=0.60,
        neutral_confidence=0.40,
    )


def test_asof_join_uses_past_state() -> None:
    assembled = assemble_historical_morphology_state(
        calendar=_calendar(),
        field=_field(),
        evolution=_evolution(),
        trajectories=_trajectory(),
        config=_config(),
    )

    assert len(assembled) == 1

    assert (
        assembled.iloc[0][
            "field_source_timestamp"
        ]
        == pd.Timestamp(
            "2026-01-01T00:45:00Z"
        )
    )


def test_supportive_state_can_be_replayed() -> None:
    assembled = assemble_historical_morphology_state(
        calendar=_calendar(),
        field=_field(),
        evolution=_evolution(),
        trajectories=_trajectory(),
        config=_config(),
    )

    decisions = build_morphology_historical_replay(
        assembled_state=assembled,
        config=_config(),
    )

    row = decisions.iloc[0]

    assert row["morphology_state"] == SUPPORTIVE
    assert row["action"] == "ENTER"
    assert row["direction"] == "LONG"
    assert bool(row["entry_ready"])


def test_receding_state_is_adverse() -> None:
    assembled = assemble_historical_morphology_state(
        calendar=_calendar(),
        field=_field(),
        evolution=_evolution(
            "RECEDING"
        ),
        trajectories=_trajectory(),
        config=_config(),
    )

    decisions = build_morphology_historical_replay(
        assembled_state=assembled,
        config=_config(),
    )

    assert (
        decisions.iloc[0][
            "morphology_state"
        ]
        == ADVERSE
    )

    assert not bool(
        decisions.iloc[0][
            "entry_ready"
        ]
    )


def test_missing_trajectory_is_neutral_or_adverse() -> None:
    assembled = assemble_historical_morphology_state(
        calendar=_calendar(),
        field=_field(),
        evolution=_evolution(),
        trajectories=pd.DataFrame(),
        config=_config(),
    )

    decisions = build_morphology_historical_replay(
        assembled_state=assembled,
        config=_config(),
    )

    assert decisions.iloc[0][
        "morphology_state"
    ] in {
        NEUTRAL,
        ADVERSE,
    }

    assert not bool(
        decisions.iloc[0][
            "entry_ready"
        ]
    )


def test_unsupported_field_is_adverse() -> None:
    assembled = assemble_historical_morphology_state(
        calendar=_calendar(),
        field=_field(
            supported=False,
        ),
        evolution=_evolution(),
        trajectories=_trajectory(),
        config=_config(),
    )

    decisions = build_morphology_historical_replay(
        assembled_state=assembled,
        config=_config(),
    )

    assert (
        decisions.iloc[0][
            "morphology_state"
        ]
        == ADVERSE
    )


def test_replay_never_authorizes_live_orders() -> None:
    assembled = assemble_historical_morphology_state(
        calendar=_calendar(),
        field=_field(),
        evolution=_evolution(),
        trajectories=_trajectory(),
        config=_config(),
    )

    decisions = build_morphology_historical_replay(
        assembled_state=assembled,
        config=_config(),
    )

    assert not decisions[
        "live_authorized"
    ].astype(bool).any()

    assert not decisions[
        "order_submission_allowed"
    ].astype(bool).any()


def test_replay_ids_are_deterministic() -> None:
    assembled = assemble_historical_morphology_state(
        calendar=_calendar(),
        field=_field(),
        evolution=_evolution(),
        trajectories=_trajectory(),
        config=_config(),
    )

    first = build_morphology_historical_replay(
        assembled_state=assembled,
        config=_config(),
    )

    second = build_morphology_historical_replay(
        assembled_state=assembled,
        config=_config(),
    )

    assert first[
        "decision_id"
    ].tolist() == second[
        "decision_id"
    ].tolist()


def test_direction_aware_selection_prefers_matching_enter() -> None:
    trajectories = pd.DataFrame([
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T00:45:00Z"
                ),
            "asset":
                "SOL",
            "recommended_action":
                "AVOID",
            "recommended_direction":
                "FLAT",
            "trajectory_score":
                1.0,
            "confidence":
                0.9,
            "observation_count":
                500,
        },
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T00:45:00Z"
                ),
            "asset":
                "SOL",
            "recommended_action":
                "ENTER",
            "recommended_direction":
                "LONG",
            "trajectory_score":
                0.1,
            "confidence":
                0.7,
            "observation_count":
                100,
        },
    ])

    assembled = assemble_historical_morphology_state(
        calendar=_calendar(),
        field=_field(),
        evolution=_evolution(),
        trajectories=trajectories,
        config=_config(),
    )

    row = assembled.iloc[0]

    assert row["recommended_action"] == "ENTER"
    assert row["recommended_direction"] == "LONG"


def test_direction_aware_selection_prefers_matching_direction() -> None:
    trajectories = pd.DataFrame([
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T00:45:00Z"
                ),
            "asset":
                "SOL",
            "recommended_action":
                "ENTER",
            "recommended_direction":
                "SHORT",
            "trajectory_score":
                1.0,
            "confidence":
                0.9,
            "observation_count":
                500,
        },
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T00:45:00Z"
                ),
            "asset":
                "SOL",
            "recommended_action":
                "ENTER",
            "recommended_direction":
                "LONG",
            "trajectory_score":
                0.1,
            "confidence":
                0.7,
            "observation_count":
                100,
        },
    ])

    assembled = assemble_historical_morphology_state(
        calendar=_calendar(),
        field=_field(),
        evolution=_evolution(),
        trajectories=trajectories,
        config=_config(),
    )

    row = assembled.iloc[0]

    assert row["recommended_direction"] == "LONG"

def test_matching_enter_inside_tolerance_beats_newer_avoid() -> None:
    trajectories = pd.DataFrame([
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T00:30:00Z"
                ),
            "asset":
                "SOL",
            "recommended_action":
                "ENTER",
            "recommended_direction":
                "LONG",
            "trajectory_score":
                0.10,
            "confidence":
                0.70,
            "observation_count":
                100,
        },
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T00:45:00Z"
                ),
            "asset":
                "SOL",
            "recommended_action":
                "AVOID",
            "recommended_direction":
                "FLAT",
            "trajectory_score":
                1.00,
            "confidence":
                0.95,
            "observation_count":
                500,
        },
    ])

    assembled = assemble_historical_morphology_state(
        calendar=_calendar(),
        field=_field(),
        evolution=_evolution(),
        trajectories=trajectories,
        config=_config(),
    )

    row = assembled.iloc[0]

    assert row["recommended_action"] == "ENTER"
    assert row["recommended_direction"] == "LONG"
    assert row["trajectory_source_timestamp"] == pd.Timestamp(
        "2026-01-01T00:30:00Z"
    )