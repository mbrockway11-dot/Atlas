"""Morphology Historical Replay Engine V1.

Builds a past-only morphology decision stream aligned to a historical event
calendar, normally the validated V32 execution replay.

The replay engine does not place orders. It produces historical morphology
assessments that can be consumed by the V32-Morphology Ensemble Bridge.

Modes
-----
shadow:
    Uses field, evolution, and trajectory evidence. Morphology may confirm,
    remain neutral, or oppose a V32 signal, but cannot independently create an
    executable order.

strict:
    Reserved for replaying fully validated morphology discovery rules. In V1,
    strict mode requires a trajectory entry plus strong field/evolution support.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SUPPORTIVE = "SUPPORTIVE"
NEUTRAL = "NEUTRAL"
ADVERSE = "ADVERSE"
UNAVAILABLE = "UNAVAILABLE"

ENTER = "ENTER"
HOLD = "HOLD"
AVOID = "AVOID"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

LONG = "LONG"
SHORT = "SHORT"
FLAT = "FLAT"


@dataclass(frozen=True, slots=True)
class MorphologyHistoricalReplayConfig:
    mode: str = "shadow"

    maximum_asof_age_bars: int = 8
    bar_minutes: int = 15

    minimum_field_predictability: float = 0.25
    supportive_field_predictability: float = 0.55
    maximum_field_strain: float = 5.0
    maximum_attractor_eta: float = 64.0

    supportive_confidence: float = 0.65
    neutral_confidence: float = 0.40

    trajectory_observation_target: int = 500
    require_supported_field: bool = True
    require_trajectory_for_support: bool = True

    research_only: bool = True

    def __post_init__(self) -> None:
        if self.mode not in {
            "shadow",
            "strict",
        }:
            raise ValueError(
                "mode must be 'shadow' or 'strict'."
            )

        if self.maximum_asof_age_bars < 1:
            raise ValueError(
                "maximum_asof_age_bars must be positive."
            )

        if self.bar_minutes < 1:
            raise ValueError(
                "bar_minutes must be positive."
            )

        for name in (
            "minimum_field_predictability",
            "supportive_field_predictability",
            "supportive_confidence",
            "neutral_confidence",
        ):
            value = float(
                getattr(self, name)
            )

            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between zero and one."
                )

        if (
            self.supportive_confidence
            < self.neutral_confidence
        ):
            raise ValueError(
                "supportive_confidence must be greater than or equal "
                "to neutral_confidence."
            )

    @property
    def asof_tolerance(self) -> pd.Timedelta:
        return pd.Timedelta(
            minutes=(
                self.maximum_asof_age_bars
                * self.bar_minutes
            )
        )


def _boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {
        "true",
        "1",
        "yes",
        "y",
    }


def _number(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default

    if not math.isfinite(result):
        return default

    return result


def _direction(value: Any) -> str:
    result = str(
        value or FLAT
    ).strip().upper()

    aliases = {
        "ENTER_LONG": LONG,
        "BUY": LONG,
        "ENTER_SHORT": SHORT,
        "SELL": SHORT,
    }

    result = aliases.get(
        result,
        result,
    )

    if result not in {
        LONG,
        SHORT,
        FLAT,
    }:
        return FLAT

    return result


def _timestamp_frame(
    path: str | Path,
    *,
    timestamp_candidates: tuple[str, ...],
) -> pd.DataFrame:
    source = Path(path)

    if not source.exists():
        raise FileNotFoundError(
            f"Replay input does not exist: {source}"
        )

    frame = pd.read_csv(
        source,
        low_memory=False,
    )

    timestamp_column = next(
        (
            column
            for column in timestamp_candidates
            if column in frame.columns
        ),
        None,
    )

    if timestamp_column is None:
        raise ValueError(
            f"No supported timestamp column in {source}"
        )

    if timestamp_column != "timestamp":
        frame = frame.rename(
            columns={
                timestamp_column:
                    "timestamp",
            }
        )

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        utc=True,
        errors="coerce",
    )

    return (
        frame.dropna(
            subset=["timestamp"]
        )
        .reset_index(drop=True)
    )


def load_replay_calendar(
    path: str | Path,
) -> pd.DataFrame:
    frame = _timestamp_frame(
        path,
        timestamp_candidates=(
            "timestamp",
            "decision_timestamp",
            "entry_time",
        ),
    )

    if "asset" not in frame.columns:
        frame["asset"] = "SOL"

    frame["asset"] = (
        frame["asset"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    action_column = next(
        (
            column
            for column in (
                "combined_action",
                "action",
            )
            if column in frame.columns
        ),
        None,
    )

    direction_column = next(
        (
            column
            for column in (
                "combined_direction",
                "direction",
            )
            if column in frame.columns
        ),
        None,
    )

    if action_column is None:
        frame["calendar_action"] = ""
    else:
        frame["calendar_action"] = (
            frame[action_column]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    if direction_column is None:
        frame["calendar_direction"] = FLAT
    else:
        frame["calendar_direction"] = frame[
            direction_column
        ].map(_direction)

    return (
        frame.sort_values(
            [
                "timestamp",
                "asset",
            ],
            kind="stable",
        )
        .drop_duplicates(
            subset=[
                "timestamp",
                "asset",
                "calendar_action",
            ],
            keep="last",
        )
        .reset_index(drop=True)
    )


def load_replay_field(
    path: str | Path,
) -> pd.DataFrame:
    frame = _timestamp_frame(
        path,
        timestamp_candidates=(
            "timestamp",
        ),
    )

    keep = [
        column
        for column in (
            "timestamp",
            "fold_id",
            "morphology_cluster_id",
            "morphology_cluster",
            "field_supported",
            "field_flow_class",
            "field_predictability",
            "field_divergence",
            "field_curl",
            "field_strain_magnitude",
            "field_attractor_pressure",
            "field_mean_closing_efficiency",
            "field_min_attractor_distance",
            "field_strong_approach_count",
            "field_high_predictability",
            "field_high_expansion",
            "field_high_contraction",
            "field_high_rotation",
            "field_high_strain",
            "field_combined_opportunity",
        )
        if column in frame.columns
    ]

    return (
        frame[keep]
        .sort_values(
            "timestamp",
            kind="stable",
        )
        .drop_duplicates(
            subset=["timestamp"],
            keep="last",
        )
        .reset_index(drop=True)
    )


def load_replay_evolution(
    path: str | Path,
) -> pd.DataFrame:
    frame = _timestamp_frame(
        path,
        timestamp_candidates=(
            "timestamp",
        ),
    )

    if "asset" not in frame.columns:
        raise ValueError(
            "Evolution replay input requires asset."
        )

    frame["asset"] = (
        frame["asset"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    preferred = [
        column
        for column in (
            "timestamp",
            "asset",
            "morphology_cluster",
            "morphology_cluster_id",
            "morphology_motion_state",
            "morphology_speed",
            "morphology_acceleration_magnitude",
            "morphology_curvature",
            "morphology_directional_stability",
            "attractor_cluster",
            "attractor_cluster_id",
            "attractor_strength",
            "distance_to_attractor",
            "attractor_closing_velocity",
            "approaching_attractor",
            "estimated_bars_to_attractor",
            "attractor_alignment_score",
            "evolution_signal",
        )
        if column in frame.columns
    ]

    result = frame[preferred].copy()

    if "attractor_rank" in frame.columns:
        frame["attractor_rank"] = pd.to_numeric(
            frame["attractor_rank"],
            errors="coerce",
        ).fillna(999999)

        frame = frame.sort_values(
            [
                "timestamp",
                "asset",
                "attractor_rank",
            ],
            kind="stable",
        )

        result = frame[
            preferred
        ].drop_duplicates(
            subset=[
                "timestamp",
                "asset",
            ],
            keep="first",
        )

    return (
        result.sort_values(
            [
                "asset",
                "timestamp",
            ],
            kind="stable",
        )
        .drop_duplicates(
            subset=[
                "timestamp",
                "asset",
            ],
            keep="first",
        )
        .reset_index(drop=True)
    )


def load_replay_trajectories(
    path: str | Path,
) -> pd.DataFrame:
    frame = _timestamp_frame(
        path,
        timestamp_candidates=(
            "timestamp",
            "window_end",
            "entry_timestamp",
        ),
    )

    if "asset" not in frame.columns:
        raise ValueError(
            "Trajectory replay input requires asset."
        )

    frame["asset"] = (
        frame["asset"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    if "recommended_action" not in frame.columns:
        frame["recommended_action"] = ""

    if "recommended_direction" not in frame.columns:
        frame["recommended_direction"] = FLAT

    frame["recommended_action"] = (
        frame["recommended_action"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    frame["recommended_direction"] = frame[
        "recommended_direction"
    ].map(_direction)

    for column in (
        "trajectory_score",
        "observation_count",
        "preferred_mean_return",
        "preferred_win_rate",
        "confidence",
    ):
        if column not in frame.columns:
            frame[column] = 0.0

        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        ).fillna(0.0)

    # Keep all trajectory candidates. Selection must happen after the replay
    # calendar direction is known.
    return (
        frame.sort_values(
            [
                "asset",
                "timestamp",
                "trajectory_score",
                "observation_count",
            ],
            ascending=[
                True,
                True,
                False,
                False,
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def _asof_global(
    calendar: pd.DataFrame,
    source: pd.DataFrame,
    *,
    tolerance: pd.Timedelta,
    suffix: str,
) -> pd.DataFrame:
    if source.empty:
        return calendar.copy()

    left = calendar.sort_values(
        "timestamp",
        kind="stable",
    )

    right = source.sort_values(
        "timestamp",
        kind="stable",
    )

    source_time_column = (
        f"{suffix}_source_timestamp"
    )

    right = right.rename(
        columns={
            "timestamp":
                source_time_column,
        }
    )

    merged = pd.merge_asof(
        left,
        right,
        left_on="timestamp",
        right_on=source_time_column,
        direction="backward",
        tolerance=tolerance,
        allow_exact_matches=True,
    )

    return merged


def _asof_by_asset(
    calendar: pd.DataFrame,
    source: pd.DataFrame,
    *,
    tolerance: pd.Timedelta,
    suffix: str,
) -> pd.DataFrame:
    if source.empty:
        return calendar.copy()

    source_time_column = (
        f"{suffix}_source_timestamp"
    )

    right = source.rename(
        columns={
            "timestamp":
                source_time_column,
        }
    )

    groups = []

    for asset, left_group in calendar.groupby(
        "asset",
        sort=True,
        observed=True,
    ):
        right_group = right[
            right["asset"].eq(asset)
        ].drop(
            columns=["asset"],
            errors="ignore",
        )

        left_group = left_group.sort_values(
            "timestamp",
            kind="stable",
        )

        right_group = right_group.sort_values(
            source_time_column,
            kind="stable",
        )

        if right_group.empty:
            groups.append(
                left_group
            )

            continue

        merged = pd.merge_asof(
            left_group,
            right_group,
            left_on="timestamp",
            right_on=source_time_column,
            direction="backward",
            tolerance=tolerance,
            allow_exact_matches=True,
        )

        groups.append(
            merged
        )

    if not groups:
        return calendar.copy()

    return (
        pd.concat(
            groups,
            ignore_index=True,
        )
        .sort_values(
            [
                "timestamp",
                "asset",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def _select_trajectory_for_event(
    candidates: pd.DataFrame,
    *,
    calendar_direction: str,
) -> pd.Series | None:
    if candidates.empty:
        return None

    frame = candidates.copy()

    defaults = {
        "trajectory_score": 0.0,
        "confidence": 0.0,
        "observation_count": 0,
        "recommended_action": "",
        "recommended_direction": FLAT,
    }

    for column, default in defaults.items():
        if column not in frame.columns:
            frame[column] = default

    frame["trajectory_score"] = pd.to_numeric(
        frame["trajectory_score"],
        errors="coerce",
    ).fillna(0.0)

    frame["confidence"] = pd.to_numeric(
        frame["confidence"],
        errors="coerce",
    ).fillna(0.0)

    frame["observation_count"] = pd.to_numeric(
        frame["observation_count"],
        errors="coerce",
    ).fillna(0)

    frame["recommended_action"] = (
        frame["recommended_action"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    frame["recommended_direction"] = frame[
        "recommended_direction"
    ].map(_direction)

    desired_direction = _direction(
        calendar_direction
    )

    frame["_action_rank"] = np.select(
        [
            frame["recommended_action"].eq(ENTER)
            & frame["recommended_direction"].eq(
                desired_direction
            ),
            frame["recommended_action"].eq(ENTER),
            frame["recommended_action"].eq(AVOID),
            frame["recommended_action"].eq(
                INSUFFICIENT_EVIDENCE
            ),
        ],
        [
            4,
            3,
            2,
            1,
        ],
        default=0,
    )

    frame["_direction_rank"] = (
        frame["recommended_direction"]
        .eq(desired_direction)
        .astype(int)
    )

    sort_columns = [
        "_action_rank",
        "_direction_rank",
    ]

    if "timestamp" in frame.columns:
        sort_columns.append(
            "timestamp"
        )

    for column in (
        "trajectory_score",
        "confidence",
        "observation_count",
    ):
        if column in frame.columns:
            sort_columns.append(column)

    ranked = frame.sort_values(
        sort_columns,
        ascending=[
            False
        ] * len(sort_columns),
        kind="stable",
    )

    return ranked.iloc[0]


def _attach_direction_aware_trajectories(
    calendar: pd.DataFrame,
    trajectories: pd.DataFrame,
    *,
    tolerance: pd.Timedelta,
) -> pd.DataFrame:
    if trajectories.empty:
        return calendar.copy()

    rows: list[dict[str, Any]] = []

    for calendar_row in calendar.to_dict(
        orient="records"
    ):
        timestamp = pd.Timestamp(
            calendar_row["timestamp"]
        )

        asset = str(
            calendar_row["asset"]
        ).upper()

        minimum_timestamp = (
            timestamp - tolerance
        )

        candidates = trajectories[
            trajectories["asset"].eq(asset)
            & trajectories["timestamp"].le(
                timestamp
            )
            & trajectories["timestamp"].ge(
                minimum_timestamp
            )
        ]

        selected = _select_trajectory_for_event(
            candidates,
            calendar_direction=str(
                calendar_row.get(
                    "calendar_direction",
                    FLAT,
                )
            ),
        )

        output = dict(calendar_row)

        if selected is not None:
            output[
                "trajectory_source_timestamp"
            ] = selected["timestamp"]

            for column, value in selected.items():
                if column in {
                    "timestamp",
                    "asset",
                    "_action_rank",
                    "_direction_rank",
                }:
                    continue

                output[column] = value

        rows.append(output)

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "timestamp",
                "asset",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )

def assemble_historical_morphology_state(
    *,
    calendar: pd.DataFrame,
    field: pd.DataFrame,
    evolution: pd.DataFrame,
    trajectories: pd.DataFrame,
    config: MorphologyHistoricalReplayConfig,
) -> pd.DataFrame:
    result = _asof_global(
        calendar,
        field,
        tolerance=config.asof_tolerance,
        suffix="field",
    )

    result = _asof_by_asset(
        result,
        evolution,
        tolerance=config.asof_tolerance,
        suffix="evolution",
    )

    result = _attach_direction_aware_trajectories(
        result,
        trajectories,
        tolerance=config.asof_tolerance,
    )

    return result


def score_historical_state(
    row: pd.Series,
    *,
    config: MorphologyHistoricalReplayConfig,
) -> dict[str, Any]:
    reasons: list[str] = []

    field_timestamp = row.get(
        "field_source_timestamp"
    )

    evolution_timestamp = row.get(
        "evolution_source_timestamp"
    )

    trajectory_timestamp = row.get(
        "trajectory_source_timestamp"
    )

    available_layers = sum(
        pd.notna(value)
        for value in (
            field_timestamp,
            evolution_timestamp,
            trajectory_timestamp,
        )
    )

    if available_layers == 0:
        return {
            "morphology_state":
                UNAVAILABLE,
            "action":
                INSUFFICIENT_EVIDENCE,
            "direction":
                FLAT,
            "entry_ready":
                False,
            "confidence":
                0.0,
            "target_exposure":
                0.0,
            "reasons":
                ["no_historical_morphology_state"],
        }

    score = 0.50

    field_supported = _boolean(
        row.get(
            "field_supported",
            False,
        )
    )

    predictability = _number(
        row.get(
            "field_predictability",
            0.0,
        )
    )

    strain = _number(
        row.get(
            "field_strain_magnitude",
            0.0,
        )
    )

    if field_supported:
        score += 0.10
        reasons.append(
            "field_supported"
        )
    else:
        score -= 0.30
        reasons.append(
            "field_unsupported"
        )

    if (
        predictability
        >= config.supportive_field_predictability
    ):
        score += 0.15
        reasons.append(
            "field_predictability_supportive"
        )
    elif (
        predictability
        < config.minimum_field_predictability
    ):
        score -= 0.15
        reasons.append(
            "field_predictability_low"
        )

    if strain > config.maximum_field_strain:
        score -= 0.15
        reasons.append(
            "field_strain_high"
        )

    evolution_signal = str(
        row.get(
            "evolution_signal",
            "",
        )
    ).strip().upper()

    evolution_adjustment = {
        "STRONG_APPROACH": 0.20,
        "APPROACH": 0.15,
        "APPROACHING_STABLE": 0.15,
        "WEAK_APPROACH": 0.05,
        "TANGENTIAL": 0.0,
        "WEAK_RECESSION": -0.10,
        "RECEDING": -0.25,
    }.get(
        evolution_signal,
        0.0,
    )

    score += evolution_adjustment

    if evolution_signal:
        reasons.append(
            "evolution_"
            + evolution_signal.lower()
        )

    eta = _number(
        row.get(
            "estimated_bars_to_attractor",
            config.maximum_attractor_eta,
        ),
        config.maximum_attractor_eta,
    )

    if eta <= config.maximum_attractor_eta:
        score += 0.05
        reasons.append(
            "attractor_eta_supported"
        )
    else:
        score -= 0.10
        reasons.append(
            "attractor_eta_long"
        )

    trajectory_action = str(
        row.get(
            "recommended_action",
            "",
        )
    ).strip().upper()

    trajectory_direction = _direction(
        row.get(
            "recommended_direction",
            row.get(
                "direction",
                FLAT,
            ),
        )
    )

    trajectory_score = _number(
        row.get(
            "trajectory_score",
            0.0,
        )
    )

    trajectory_observations = int(
        max(
            _number(
                row.get(
                    "observation_count",
                    0,
                )
            ),
            0.0,
        )
    )

    trajectory_enter = bool(
        trajectory_action == ENTER
        and trajectory_direction
        in {
            LONG,
            SHORT,
        }
    )

    if trajectory_enter:
        score += 0.15
        reasons.append(
            "trajectory_entry_support"
        )

        observation_support = min(
            trajectory_observations
            / max(
                config.trajectory_observation_target,
                1,
            ),
            1.0,
        )

        score += (
            0.05
            * observation_support
        )

        if trajectory_score > 0.0:
            score += min(
                trajectory_score
                * 100.0,
                0.05,
            )
    else:
        reasons.append(
            "trajectory_no_entry"
        )

    hard_adverse = bool(
        (
            config.require_supported_field
            and not field_supported
        )
        or evolution_signal
        in {
            "RECEDING",
        }
        or strain
        > config.maximum_field_strain
    )

    confidence = float(
        np.clip(
            score,
            0.0,
            1.0,
        )
    )

    supportive = bool(
        not hard_adverse
        and confidence
        >= config.supportive_confidence
        and (
            trajectory_enter
            or not config.require_trajectory_for_support
        )
    )

    if supportive:
        morphology_state = SUPPORTIVE
        action = ENTER
        direction = trajectory_direction
        entry_ready = True
    elif (
        hard_adverse
        or confidence
        < config.neutral_confidence
    ):
        morphology_state = ADVERSE
        action = AVOID
        direction = FLAT
        entry_ready = False
    else:
        morphology_state = NEUTRAL
        action = HOLD
        direction = FLAT
        entry_ready = False

    return {
        "morphology_state":
            morphology_state,
        "action":
            action,
        "direction":
            direction,
        "entry_ready":
            entry_ready,
        "confidence":
            confidence,
        "target_exposure":
            0.0,
        "reasons":
            sorted(
                set(reasons)
            ),
    }


def replay_decision_id(
    payload: dict[str, Any],
) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    digest = hashlib.sha256(
        canonical.encode(
            "utf-8"
        )
    ).hexdigest()[:24]

    return (
        f"MORPH-REPLAY-{digest}"
    )


def build_morphology_historical_replay(
    *,
    assembled_state: pd.DataFrame,
    config: MorphologyHistoricalReplayConfig = (
        MorphologyHistoricalReplayConfig()
    ),
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for source_row in assembled_state.to_dict(
        orient="records"
    ):
        row = pd.Series(
            source_row
        )

        assessment = score_historical_state(
            row,
            config=config,
        )

        timestamp = pd.Timestamp(
            source_row["timestamp"]
        )

        payload = {
            "schema_version":
                "atlas.morphology_historical_replay.v1",
            "timestamp":
                timestamp.isoformat(),
            "asset":
                str(
                    source_row.get(
                        "asset",
                        "",
                    )
                ).upper(),
            "calendar_action":
                str(
                    source_row.get(
                        "calendar_action",
                        "",
                    )
                ),
            "calendar_direction":
                str(
                    source_row.get(
                        "calendar_direction",
                        FLAT,
                    )
                ),
            "morphology_state":
                assessment[
                    "morphology_state"
                ],
            "action":
                assessment["action"],
            "direction":
                assessment["direction"],
            "entry_ready":
                assessment[
                    "entry_ready"
                ],
            "confidence":
                assessment[
                    "confidence"
                ],
            "target_exposure":
                assessment[
                    "target_exposure"
                ],
            "field_source_timestamp":
                source_row.get(
                    "field_source_timestamp",
                    "",
                ),
            "evolution_source_timestamp":
                source_row.get(
                    "evolution_source_timestamp",
                    "",
                ),
            "trajectory_source_timestamp":
                source_row.get(
                    "trajectory_source_timestamp",
                    "",
                ),
            "morphology_cluster_id":
                source_row.get(
                    "morphology_cluster_id",
                    "",
                ),
            "field_supported":
                _boolean(
                    source_row.get(
                        "field_supported",
                        False,
                    )
                ),
            "field_predictability":
                _number(
                    source_row.get(
                        "field_predictability",
                        0.0,
                    )
                ),
            "field_flow_class":
                str(
                    source_row.get(
                        "field_flow_class",
                        "",
                    )
                ),
            "field_divergence":
                _number(
                    source_row.get(
                        "field_divergence",
                        0.0,
                    )
                ),
            "field_curl":
                _number(
                    source_row.get(
                        "field_curl",
                        0.0,
                    )
                ),
            "field_strain_magnitude":
                _number(
                    source_row.get(
                        "field_strain_magnitude",
                        0.0,
                    )
                ),
            "evolution_signal":
                str(
                    source_row.get(
                        "evolution_signal",
                        "",
                    )
                ),
            "estimated_bars_to_attractor":
                _number(
                    source_row.get(
                        "estimated_bars_to_attractor",
                        0.0,
                    )
                ),
            "recommended_action":
                str(
                    source_row.get(
                        "recommended_action",
                        "",
                    )
                ),
            "recommended_direction":
                _direction(
                    source_row.get(
                        "recommended_direction",
                        FLAT,
                    )
                ),
            "trajectory_score":
                _number(
                    source_row.get(
                        "trajectory_score",
                        0.0,
                    )
                ),
            "trajectory_observation_count":
                int(
                    max(
                        _number(
                            source_row.get(
                                "observation_count",
                                0,
                            )
                        ),
                        0.0,
                    )
                ),
            "reasons":
                "|".join(
                    assessment[
                        "reasons"
                    ]
                ),
            "mode":
                config.mode,
            "requires_pre_trade_risk":
                True,
            "requires_manual_approval":
                True,
            "research_only":
                bool(
                    config.research_only
                ),
            "live_authorized":
                False,
            "order_submission_allowed":
                False,
        }

        payload["decision_id"] = (
            replay_decision_id(
                payload
            )
        )

        rows.append(payload)

    if not rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "timestamp",
                "asset",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def write_morphology_historical_replay_outputs(
    *,
    decisions: pd.DataFrame,
    config: MorphologyHistoricalReplayConfig,
    output_dir: str | Path,
) -> dict[str, Path]:
    directory = Path(
        output_dir
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = (
        directory
        / "morphology_historical_replay_decisions.csv"
    )

    json_path = (
        directory
        / "morphology_historical_replay_decisions.json"
    )

    summary_path = (
        directory
        / "morphology_historical_replay_summary.json"
    )

    decisions.to_csv(
        csv_path,
        index=False,
    )

    json_path.write_text(
        json.dumps(
            decisions.to_dict(
                orient="records"
            ),
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    state_counts = (
        decisions[
            "morphology_state"
        ]
        .value_counts()
        .sort_index()
        .to_dict()
        if not decisions.empty
        else {}
    )

    summary = {
        "schema_version":
            "atlas.morphology_historical_replay_summary.v1",
        "config":
            asdict(config),
        "decision_count":
            int(len(decisions)),
        "supportive_count":
            int(
                state_counts.get(
                    SUPPORTIVE,
                    0,
                )
            ),
        "neutral_count":
            int(
                state_counts.get(
                    NEUTRAL,
                    0,
                )
            ),
        "adverse_count":
            int(
                state_counts.get(
                    ADVERSE,
                    0,
                )
            ),
        "unavailable_count":
            int(
                state_counts.get(
                    UNAVAILABLE,
                    0,
                )
            ),
        "entry_ready_count":
            int(
                decisions[
                    "entry_ready"
                ].astype(bool).sum()
            ) if not decisions.empty else 0,
        "state_counts":
            state_counts,
        "research_only":
            True,
        "live_authorized":
            False,
        "order_submission_allowed":
            False,
    }

    summary_path.write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "csv":
            csv_path,
        "json":
            json_path,
        "summary":
            summary_path,
    }
