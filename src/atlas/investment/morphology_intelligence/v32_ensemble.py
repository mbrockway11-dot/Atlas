"""V32-Morphology Ensemble Bridge V1.

Combines a primary V32 decision with Atlas morphology intelligence.

Design rules:
- V32 remains the primary signal generator.
- Morphology cannot originate a trade.
- Supportive morphology may preserve V32 exposure.
- Neutral morphology reduces exposure.
- Adverse morphology vetoes the entry.
- Exit instructions from V32 always pass through.
- No live authorization or order submission is granted here.

The output preserves the V32 combined-decision contract so it can feed Atlas's
existing intent, risk, approval, execution-simulator, and paper-trading stack.
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


NO_ACTION = "NO_ACTION"
ENTER_LONG = "ENTER_LONG"
ENTER_SHORT = "ENTER_SHORT"
EXIT_POSITION = "EXIT_POSITION"

LONG = "LONG"
SHORT = "SHORT"
FLAT = "FLAT"

SUPPORTIVE = "SUPPORTIVE"
NEUTRAL = "NEUTRAL"
ADVERSE = "ADVERSE"
UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class V32MorphologyEnsembleConfig:
    supportive_exposure_multiplier: float = 1.0
    neutral_exposure_multiplier: float = 0.50
    unavailable_exposure_multiplier: float = 0.25

    minimum_supportive_confidence: float = 0.70
    maximum_adverse_confidence: float = 0.35

    veto_on_adverse: bool = True
    veto_on_morphology_avoid: bool = True
    allow_unavailable_morphology: bool = True

    maximum_target_exposure: float = 0.10
    research_only: bool = True
    require_manual_approval: bool = True

    def __post_init__(self) -> None:
        bounded = (
            "supportive_exposure_multiplier",
            "neutral_exposure_multiplier",
            "unavailable_exposure_multiplier",
            "minimum_supportive_confidence",
            "maximum_adverse_confidence",
            "maximum_target_exposure",
        )

        for name in bounded:
            value = float(
                getattr(self, name)
            )

            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between zero and one."
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
    except (TypeError, ValueError):
        return default

    if not math.isfinite(result):
        return default

    return result


def _normalize_action(value: Any) -> str:
    action = str(value or NO_ACTION).strip().upper()

    aliases = {
        "ENTER": ENTER_LONG,
        "BUY": ENTER_LONG,
        "LONG": ENTER_LONG,
        "SELL_SHORT": ENTER_SHORT,
        "SHORT": ENTER_SHORT,
        "EXIT": EXIT_POSITION,
        "CLOSE": EXIT_POSITION,
        "FLAT": NO_ACTION,
    }

    return aliases.get(
        action,
        action,
    )


def _normalize_direction(value: Any) -> str:
    direction = str(
        value or FLAT
    ).strip().upper()

    if direction not in {
        LONG,
        SHORT,
        FLAT,
    }:
        return FLAT

    return direction


def load_v32_combined_decisions(
    path: str | Path,
) -> pd.DataFrame:
    source = Path(path)

    if not source.exists():
        raise FileNotFoundError(
            f"V32 decision file does not exist: {source}"
        )

    frame = pd.read_csv(
        source,
        low_memory=False,
    )

    timestamp_column = next(
        (
            column
            for column in (
                "timestamp",
                "decision_timestamp",
                "entry_time",
            )
            if column in frame.columns
        ),
        None,
    )

    if timestamp_column is None:
        raise ValueError(
            "V32 decisions require a timestamp column."
        )

    if timestamp_column != "timestamp":
        frame = frame.rename(
            columns={
                timestamp_column:
                    "timestamp",
            }
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

    exposure_column = next(
        (
            column
            for column in (
                "combined_target_exposure",
                "target_exposure",
            )
            if column in frame.columns
        ),
        None,
    )

    if action_column is None:
        raise ValueError(
            "V32 decisions require combined_action or action."
        )

    if direction_column is None:
        raise ValueError(
            "V32 decisions require combined_direction or direction."
        )

    if exposure_column is None:
        raise ValueError(
            "V32 decisions require target exposure."
        )

    result = frame.copy()

    result["timestamp"] = pd.to_datetime(
        result["timestamp"],
        utc=True,
        errors="coerce",
    )

    if "asset" not in result.columns:
        result["asset"] = "SOL"

    result["asset"] = (
        result["asset"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    result["combined_action"] = result[
        action_column
    ].map(_normalize_action)

    result["combined_direction"] = result[
        direction_column
    ].map(_normalize_direction)

    result["combined_target_exposure"] = (
        pd.to_numeric(
            result[exposure_column],
            errors="coerce",
        )
        .fillna(0.0)
        .clip(lower=0.0)
    )

    result["v32_entry_ready"] = (
        result["combined_action"].isin({
            ENTER_LONG,
            ENTER_SHORT,
        })
        & result[
            "combined_target_exposure"
        ].gt(0.0)
    )

    return (
        result.dropna(
            subset=["timestamp"]
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


def load_morphology_execution_decisions(
    path: str | Path,
) -> pd.DataFrame:
    source = Path(path)

    if not source.exists():
        return pd.DataFrame()

    frame = pd.read_csv(
        source,
        low_memory=False,
    )

    if frame.empty:
        return frame

    required = {
        "timestamp",
        "asset",
        "action",
        "direction",
        "confidence",
        "entry_ready",
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            "Morphology decisions are missing required columns: "
            f"{missing}"
        )

    result = frame.copy()

    result["timestamp"] = pd.to_datetime(
        result["timestamp"],
        utc=True,
        errors="coerce",
    )

    result["asset"] = (
        result["asset"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    result["action"] = (
        result["action"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    result["direction"] = result[
        "direction"
    ].map(_normalize_direction)

    result["confidence"] = (
        pd.to_numeric(
            result["confidence"],
            errors="coerce",
        )
        .fillna(0.0)
        .clip(
            lower=0.0,
            upper=1.0,
        )
    )

    result["entry_ready"] = result[
        "entry_ready"
    ].map(_boolean)

    return (
        result.dropna(
            subset=["timestamp"]
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


def morphology_assessment(
    morphology_row: pd.Series | None,
    *,
    v32_direction: str,
    config: V32MorphologyEnsembleConfig,
) -> tuple[str, float, list[str]]:
    if morphology_row is None:
        if config.allow_unavailable_morphology:
            return (
                UNAVAILABLE,
                config.unavailable_exposure_multiplier,
                ["morphology_unavailable"],
            )

        return (
            ADVERSE,
            0.0,
            ["morphology_required_but_unavailable"],
        )

    action = str(
        morphology_row.get(
            "action",
            "",
        )
    ).upper()

    direction = _normalize_direction(
        morphology_row.get(
            "direction",
            FLAT,
        )
    )

    confidence = _number(
        morphology_row.get(
            "confidence",
            0.0,
        )
    )

    entry_ready = _boolean(
        morphology_row.get(
            "entry_ready",
            False,
        )
    )

    reasons: list[str] = []

    if (
        config.veto_on_morphology_avoid
        and action == "AVOID"
    ):
        reasons.append(
            "morphology_action_avoid"
        )

        return (
            ADVERSE,
            0.0,
            reasons,
        )

    if (
        entry_ready
        and direction == v32_direction
        and confidence
        >= config.minimum_supportive_confidence
    ):
        reasons.append(
            "morphology_directional_confirmation"
        )

        return (
            SUPPORTIVE,
            config.supportive_exposure_multiplier,
            reasons,
        )

    if (
        entry_ready
        and direction not in {
            FLAT,
            v32_direction,
        }
    ):
        reasons.append(
            "morphology_direction_conflict"
        )

        return (
            ADVERSE,
            0.0,
            reasons,
        )

    if confidence <= config.maximum_adverse_confidence:
        reasons.append(
            "morphology_confidence_low"
        )

        return (
            ADVERSE,
            0.0,
            reasons,
        )

    reasons.append(
        "morphology_neutral"
    )

    return (
        NEUTRAL,
        config.neutral_exposure_multiplier,
        reasons,
    )


def ensemble_decision_id(
    payload: dict[str, Any],
) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    digest = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()[:24]

    return f"V32-MORPH-{digest}"


def _latest_morphology_at_or_before(
    morphology: pd.DataFrame,
    *,
    asset: str,
    timestamp: pd.Timestamp,
) -> pd.Series | None:
    if morphology.empty:
        return None

    rows = morphology[
        morphology["asset"].eq(asset)
        & morphology["timestamp"].le(
            timestamp
        )
    ]

    if rows.empty:
        return None

    return rows.iloc[-1]


def build_v32_morphology_ensemble(
    *,
    v32_decisions: pd.DataFrame,
    morphology_decisions: pd.DataFrame,
    config: V32MorphologyEnsembleConfig = (
        V32MorphologyEnsembleConfig()
    ),
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for v32_row in v32_decisions.itertuples(
        index=False
    ):
        timestamp = pd.Timestamp(
            v32_row.timestamp
        )

        asset = str(
            v32_row.asset
        ).upper()

        v32_action = _normalize_action(
            v32_row.combined_action
        )

        v32_direction = _normalize_direction(
            v32_row.combined_direction
        )

        v32_exposure = min(
            max(
                _number(
                    v32_row.combined_target_exposure
                ),
                0.0,
            ),
            config.maximum_target_exposure,
        )

        morphology_row = (
            _latest_morphology_at_or_before(
                morphology_decisions,
                asset=asset,
                timestamp=timestamp,
            )
        )

        morphology_state = UNAVAILABLE
        morphology_multiplier = 0.0
        reasons: list[str] = []

        if v32_action == EXIT_POSITION:
            ensemble_action = EXIT_POSITION
            ensemble_direction = FLAT
            ensemble_exposure = 0.0
            ensemble_entry_ready = False

            morphology_state = "BYPASSED_FOR_EXIT"
            reasons.append(
                "v32_exit_pass_through"
            )

        elif v32_action not in {
            ENTER_LONG,
            ENTER_SHORT,
        }:
            ensemble_action = NO_ACTION
            ensemble_direction = FLAT
            ensemble_exposure = 0.0
            ensemble_entry_ready = False

            morphology_state = "NOT_EVALUATED"
            reasons.append(
                "v32_has_no_entry"
            )

        else:
            expected_direction = (
                LONG
                if v32_action == ENTER_LONG
                else SHORT
            )

            (
                morphology_state,
                morphology_multiplier,
                morphology_reasons,
            ) = morphology_assessment(
                morphology_row,
                v32_direction=expected_direction,
                config=config,
            )

            reasons.extend(
                morphology_reasons
            )

            vetoed = bool(
                morphology_state == ADVERSE
                and config.veto_on_adverse
            )

            if vetoed:
                ensemble_action = NO_ACTION
                ensemble_direction = FLAT
                ensemble_exposure = 0.0
                ensemble_entry_ready = False

                reasons.append(
                    "morphology_veto"
                )
            else:
                ensemble_action = v32_action
                ensemble_direction = expected_direction
                ensemble_exposure = float(
                    np.clip(
                        v32_exposure
                        * morphology_multiplier,
                        0.0,
                        config.maximum_target_exposure,
                    )
                )

                ensemble_entry_ready = bool(
                    ensemble_exposure > 0.0
                )

                reasons.append(
                    "v32_entry_retained"
                )

        morphology_confidence = (
            _number(
                morphology_row.get(
                    "confidence",
                    0.0,
                )
            )
            if morphology_row is not None
            else 0.0
        )

        source_morphology_decision_id = (
            str(
                morphology_row.get(
                    "decision_id",
                    "",
                )
            )
            if morphology_row is not None
            else ""
        )

        payload = {
            "schema_version":
                "atlas.v32_morphology_ensemble.v1",
            "timestamp":
                timestamp.isoformat(),
            "asset":
                asset,
            "v32_action":
                v32_action,
            "v32_direction":
                v32_direction,
            "v32_target_exposure":
                v32_exposure,
            "v32_entry_ready":
                bool(
                    v32_action in {
                        ENTER_LONG,
                        ENTER_SHORT,
                    }
                    and v32_exposure > 0.0
                ),
            "morphology_state":
                morphology_state,
            "morphology_confidence":
                morphology_confidence,
            "morphology_multiplier":
                morphology_multiplier,
            "morphology_veto":
                bool(
                    morphology_state == ADVERSE
                    and config.veto_on_adverse
                ),
            "combined_action":
                ensemble_action,
            "combined_direction":
                ensemble_direction,
            "combined_target_exposure":
                ensemble_exposure,
            "target_exposure":
                ensemble_exposure,
            "entry_ready":
                ensemble_entry_ready,
            "signal_state":
                (
                    "ENTRY_READY"
                    if ensemble_entry_ready
                    else (
                        "EXIT_READY"
                        if ensemble_action
                        == EXIT_POSITION
                        else "IDLE"
                    )
                ),
            "source_morphology_decision_id":
                source_morphology_decision_id,
            "requires_pre_trade_risk":
                True,
            "requires_manual_approval":
                bool(
                    config.require_manual_approval
                ),
            "research_only":
                bool(
                    config.research_only
                ),
            "live_authorized":
                False,
            "order_submission_allowed":
                False,
            "reasons":
                "|".join(
                    sorted(
                        set(reasons)
                    )
                ),
        }

        payload["ensemble_decision_id"] = (
            ensemble_decision_id(
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


def write_v32_morphology_ensemble_outputs(
    *,
    decisions: pd.DataFrame,
    config: V32MorphologyEnsembleConfig,
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
        / "v32_morphology_ensemble_decisions.csv"
    )

    json_path = (
        directory
        / "v32_morphology_ensemble_decisions.json"
    )

    summary_path = (
        directory
        / "v32_morphology_ensemble_summary.json"
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

    summary = {
        "schema_version":
            "atlas.v32_morphology_ensemble_summary.v1",
        "config":
            asdict(config),
        "decision_count":
            int(len(decisions)),
        "v32_entry_count":
            int(
                decisions[
                    "v32_entry_ready"
                ].astype(bool).sum()
            ) if not decisions.empty else 0,
        "ensemble_entry_count":
            int(
                decisions[
                    "entry_ready"
                ].astype(bool).sum()
            ) if not decisions.empty else 0,
        "morphology_veto_count":
            int(
                decisions[
                    "morphology_veto"
                ].astype(bool).sum()
            ) if not decisions.empty else 0,
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
        "csv": csv_path,
        "json": json_path,
        "summary": summary_path,
    }
