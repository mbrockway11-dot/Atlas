"""Morphology execution-decision synthesis.

This module converts validated morphology research outputs into a deterministic
decision artifact suitable for Atlas's existing portfolio-intent and execution
control plane.

It does not:
- connect to an exchange;
- place, amend, or cancel orders;
- bypass portfolio allocation;
- bypass pre-trade risk;
- bypass approval controls;
- authorize live capital.

The output is an upstream decision recommendation only.
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


ENTER = "ENTER"
EXIT = "EXIT"
HOLD = "HOLD"
AVOID = "AVOID"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

LONG = "LONG"
SHORT = "SHORT"
FLAT = "FLAT"


@dataclass(frozen=True, slots=True)
class MorphologyExecutionConfig:
    maximum_target_exposure: float = 0.10
    minimum_entry_confidence: float = 0.70
    minimum_hold_confidence: float = 0.50
    minimum_discovery_validation_folds: int = 4
    minimum_positive_uplift_rate: float = 0.60
    maximum_adjusted_p_value: float = 0.10
    minimum_net_return: float = 0.0
    minimum_incremental_uplift: float = 0.0
    minimum_field_predictability: float = 0.25
    maximum_field_strain: float = 5.0
    maximum_attractor_eta: float = 64.0
    require_supported_field: bool = True
    require_validated_discovery: bool = True
    allow_short: bool = False
    research_only: bool = True

    def __post_init__(self) -> None:
        bounded = (
            "maximum_target_exposure",
            "minimum_entry_confidence",
            "minimum_hold_confidence",
            "minimum_positive_uplift_rate",
            "maximum_adjusted_p_value",
            "minimum_field_predictability",
        )

        for name in bounded:
            value = float(
                getattr(self, name)
            )

            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between zero and one."
                )

        if self.minimum_discovery_validation_folds < 1:
            raise ValueError(
                "minimum_discovery_validation_folds must be positive."
            )

        if self.maximum_field_strain <= 0.0:
            raise ValueError(
                "maximum_field_strain must be positive."
            )

        if self.maximum_attractor_eta <= 0.0:
            raise ValueError(
                "maximum_attractor_eta must be positive."
            )


def _read_csv(
    path: str | Path,
) -> pd.DataFrame:
    source = Path(path)

    if not source.exists():
        return pd.DataFrame()

    return pd.read_csv(
        source,
        low_memory=False,
    )


def _boolean(
    value: Any,
) -> bool:
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


def _latest_rows(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    if frame.empty or "timestamp" not in frame.columns:
        return frame.copy()

    result = frame.copy()

    result["timestamp"] = pd.to_datetime(
        result["timestamp"],
        utc=True,
        errors="coerce",
    )

    result = result.dropna(
        subset=["timestamp"]
    )

    if result.empty:
        return result

    latest = result[
        "timestamp"
    ].max()

    return (
        result[
            result["timestamp"].eq(
                latest
            )
        ]
        .reset_index(drop=True)
    )


def load_latest_trajectories(
    path: str | Path,
) -> pd.DataFrame:
    frame = _read_csv(path)

    if frame.empty:
        return frame

    if "window_end" in frame.columns:
        frame = frame.rename(
            columns={
                "window_end":
                    "timestamp",
            }
        )

    return _latest_rows(
        frame
    )


def load_latest_evolution(
    path: str | Path,
) -> pd.DataFrame:
    return _latest_rows(
        _read_csv(path)
    )


def load_latest_field(
    path: str | Path,
) -> pd.DataFrame:
    return _latest_rows(
        _read_csv(path)
    )


def load_validated_discovery(
    path: str | Path,
) -> pd.DataFrame:
    frame = _read_csv(path)

    if frame.empty:
        return frame

    if "validated" in frame.columns:
        frame = frame[
            frame[
                "validated"
            ].map(_boolean)
        ]

    return frame.reset_index(
        drop=True
    )


def normalized_score(
    value: float,
    *,
    lower: float,
    upper: float,
) -> float:
    if upper <= lower:
        return 0.0

    return float(
        np.clip(
            (
                value - lower
            )
            / (
                upper - lower
            ),
            0.0,
            1.0,
        )
    )


def discovery_score(
    row: pd.Series,
    *,
    config: MorphologyExecutionConfig,
) -> float:
    folds = _number(
        row.get(
            "validation_fold_count",
            0,
        )
    )

    uplift_rate = _number(
        row.get(
            "validation_positive_uplift_rate",
            0.0,
        )
    )

    net_return = _number(
        row.get(
            "validation_net_return",
            0.0,
        )
    )

    uplift = _number(
        row.get(
            "validation_weighted_uplift",
            0.0,
        )
    )

    adjusted_p = _number(
        row.get(
            "validation_bh_adjusted_p_value",
            1.0,
        ),
        1.0,
    )

    fold_score = normalized_score(
        folds,
        lower=float(
            config.minimum_discovery_validation_folds
        ),
        upper=float(
            config.minimum_discovery_validation_folds
            * 3
        ),
    )

    uplift_rate_score = normalized_score(
        uplift_rate,
        lower=config.minimum_positive_uplift_rate,
        upper=1.0,
    )

    return_score = normalized_score(
        net_return,
        lower=config.minimum_net_return,
        upper=0.01,
    )

    uplift_score = normalized_score(
        uplift,
        lower=config.minimum_incremental_uplift,
        upper=0.005,
    )

    significance_score = float(
        np.clip(
            1.0
            - adjusted_p
            / max(
                config.maximum_adjusted_p_value,
                1e-12,
            ),
            0.0,
            1.0,
        )
    )

    return float(
        0.20 * fold_score
        + 0.25 * uplift_rate_score
        + 0.20 * return_score
        + 0.20 * uplift_score
        + 0.15 * significance_score
    )


def discovery_is_eligible(
    row: pd.Series,
    *,
    config: MorphologyExecutionConfig,
) -> bool:
    direction = str(
        row.get(
            "direction",
            FLAT,
        )
    ).upper()

    if (
        direction == SHORT
        and not config.allow_short
    ):
        return False

    return bool(
        _boolean(
            row.get(
                "validated",
                False,
            )
        )
        and _number(
            row.get(
                "validation_fold_count",
                0,
            )
        )
        >= config.minimum_discovery_validation_folds
        and _number(
            row.get(
                "validation_positive_uplift_rate",
                0.0,
            )
        )
        >= config.minimum_positive_uplift_rate
        and _number(
            row.get(
                "validation_net_return",
                0.0,
            )
        )
        > config.minimum_net_return
        and _number(
            row.get(
                "validation_weighted_uplift",
                0.0,
            )
        )
        > config.minimum_incremental_uplift
        and _number(
            row.get(
                "validation_bh_adjusted_p_value",
                1.0,
            ),
            1.0,
        )
        <= config.maximum_adjusted_p_value
    )


def expression_matches_latest(
    expression: str,
    *,
    field_row: pd.Series,
    evolution_row: pd.Series,
) -> bool:
    expression = str(
        expression
    ).strip()

    if not expression:
        return False

    clauses = [
        clause.strip()
        for clause in expression.split(
            " AND "
        )
    ]

    combined = {
        **field_row.to_dict(),
        **evolution_row.to_dict(),
    }

    for clause in clauses:
        if " == " not in clause:
            return False

        feature, expected = [
            part.strip()
            for part in clause.split(
                " == ",
                1,
            )
        ]

        if feature not in combined:
            return False

        actual = combined[feature]

        if expected in {
            "True",
            "False",
        }:
            if _boolean(actual) != (
                expected == "True"
            ):
                return False
        elif str(actual) != expected:
            return False

    return True


def field_gate(
    row: pd.Series,
    *,
    config: MorphologyExecutionConfig,
) -> tuple[bool, list[str]]:
    reasons = []

    supported = _boolean(
        row.get(
            "field_supported",
            True,
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

    if (
        config.require_supported_field
        and not supported
    ):
        reasons.append(
            "field_not_supported"
        )

    if (
        predictability
        < config.minimum_field_predictability
    ):
        reasons.append(
            "field_predictability_too_low"
        )

    if strain > config.maximum_field_strain:
        reasons.append(
            "field_strain_too_high"
        )

    return (
        not reasons,
        reasons,
    )


def evolution_gate(
    row: pd.Series,
    *,
    config: MorphologyExecutionConfig,
) -> tuple[bool, list[str]]:
    reasons = []

    signal = str(
        row.get(
            "evolution_signal",
            "NEUTRAL",
        )
    ).upper()

    eta = _number(
        row.get(
            "estimated_bars_to_attractor",
            config.maximum_attractor_eta,
        ),
        config.maximum_attractor_eta,
    )

    if signal in {
        "RECEDING",
        "WEAK_RECESSION",
    }:
        reasons.append(
            "receding_from_attractor"
        )

    if eta > config.maximum_attractor_eta:
        reasons.append(
            "attractor_eta_too_long"
        )

    return (
        not reasons,
        reasons,
    )


def trajectory_score(
    row: pd.Series | None,
) -> float:
    if row is None:
        return 0.0

    action = str(
        row.get(
            "recommended_action",
            "",
        )
    ).upper()

    score = _number(
        row.get(
            "trajectory_score",
            0.0,
        )
    )

    observations = _number(
        row.get(
            "observation_count",
            0,
        )
    )

    if action != ENTER:
        return 0.0

    return float(
        np.clip(
            0.60
            + min(
                observations / 1000.0,
                0.25,
            )
            + min(
                max(
                    score,
                    0.0,
                )
                * 100.0,
                0.15,
            ),
            0.0,
            1.0,
        )
    )


def decision_id(
    payload: dict[str, Any],
) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        default=str,
    )

    digest = hashlib.sha256(
        canonical.encode(
            "utf-8"
        )
    ).hexdigest()[:24]

    return (
        f"MORPH-DEC-{digest}"
    )


def build_asset_decision(
    *,
    asset: str,
    field_row: pd.Series,
    evolution_row: pd.Series,
    trajectory_row: pd.Series | None,
    discovery: pd.DataFrame,
    config: MorphologyExecutionConfig,
) -> dict[str, Any]:
    if (
        discovery.empty
        or "asset" not in discovery.columns
    ):
        eligible_discovery = pd.DataFrame(
            columns=discovery.columns
        )
    else:
        eligible_discovery = discovery[
            discovery[
                "asset"
            ].astype(str).str.upper().eq(
                asset
            )
        ].copy()

    if config.require_validated_discovery:
        eligible_discovery = eligible_discovery[
            eligible_discovery.apply(
                lambda row: discovery_is_eligible(
                    row,
                    config=config,
                ),
                axis=1,
            )
        ]

    if not eligible_discovery.empty:
        eligible_discovery[
            "matches_latest"
        ] = eligible_discovery.apply(
            lambda row: expression_matches_latest(
                str(
                    row.get(
                        "expression",
                        "",
                    )
                ),
                field_row=field_row,
                evolution_row=evolution_row,
            ),
            axis=1,
        )

        eligible_discovery = eligible_discovery[
            eligible_discovery[
                "matches_latest"
            ]
        ]

    field_ok, field_reasons = field_gate(
        field_row,
        config=config,
    )

    evolution_ok, evolution_reasons = evolution_gate(
        evolution_row,
        config=config,
    )

    reasons = [
        *field_reasons,
        *evolution_reasons,
    ]

    if eligible_discovery.empty:
        reasons.append(
            "no_validated_discovery_match"
        )

        direction = FLAT
        discovery_confidence = 0.0
        selected_expression = ""
        validation_net_return = 0.0
        validation_uplift = 0.0
        validation_folds = 0
    else:
        eligible_discovery[
            "_score"
        ] = eligible_discovery.apply(
            lambda row: discovery_score(
                row,
                config=config,
            ),
            axis=1,
        )

        selected = eligible_discovery.sort_values(
            [
                "_score",
                "validation_weighted_uplift",
            ],
            ascending=[
                False,
                False,
            ],
            kind="stable",
        ).iloc[0]

        direction = str(
            selected.get(
                "direction",
                FLAT,
            )
        ).upper()

        discovery_confidence = float(
            selected["_score"]
        )

        selected_expression = str(
            selected.get(
                "expression",
                "",
            )
        )

        validation_net_return = _number(
            selected.get(
                "validation_net_return",
                0.0,
            )
        )

        validation_uplift = _number(
            selected.get(
                "validation_weighted_uplift",
                0.0,
            )
        )

        validation_folds = int(
            _number(
                selected.get(
                    "validation_fold_count",
                    0,
                )
            )
        )

    trajectory_confidence = trajectory_score(
        trajectory_row
    )

    field_confidence = float(
        np.clip(
            _number(
                field_row.get(
                    "field_predictability",
                    0.0,
                )
            ),
            0.0,
            1.0,
        )
    )

    evolution_signal = str(
        evolution_row.get(
            "evolution_signal",
            "NEUTRAL",
        )
    ).upper()

    evolution_confidence = {
        "STRONG_APPROACH": 1.0,
        "APPROACH": 0.80,
        "WEAK_APPROACH": 0.60,
        "TANGENTIAL": 0.35,
        "WEAK_RECESSION": 0.15,
        "RECEDING": 0.0,
    }.get(
        evolution_signal,
        0.25,
    )

    confidence = float(
        0.50 * discovery_confidence
        + 0.20 * field_confidence
        + 0.15 * evolution_confidence
        + 0.15 * trajectory_confidence
    )

    entry_ready = bool(
        direction in {
            LONG,
            SHORT,
        }
        and field_ok
        and evolution_ok
        and not eligible_discovery.empty
        and confidence
        >= config.minimum_entry_confidence
    )

    if entry_ready:
        action = ENTER

        target_exposure = float(
            np.clip(
                config.maximum_target_exposure
                * confidence,
                0.0,
                config.maximum_target_exposure,
            )
        )
    elif reasons:
        action = AVOID
        direction = FLAT
        target_exposure = 0.0
    elif confidence >= config.minimum_hold_confidence:
        action = HOLD
        direction = FLAT
        target_exposure = 0.0
    else:
        action = INSUFFICIENT_EVIDENCE
        direction = FLAT
        target_exposure = 0.0

    timestamp = field_row.get(
        "timestamp",
        evolution_row.get(
            "timestamp",
            "",
        ),
    )

    payload = {
        "schema_version":
            "atlas.morphology_execution_decision.v1",
        "timestamp":
            str(timestamp),
        "asset":
            asset,
        "action":
            action,
        "direction":
            direction,
        "entry_ready":
            entry_ready,
        "confidence":
            confidence,
        "target_exposure":
            target_exposure,
        "research_only":
            bool(
                config.research_only
            ),
        "live_authorized":
            False,
        "selected_expression":
            selected_expression,
        "validation_fold_count":
            validation_folds,
        "validation_net_return":
            validation_net_return,
        "validation_weighted_uplift":
            validation_uplift,
        "field_flow_class":
            str(
                field_row.get(
                    "field_flow_class",
                    "",
                )
            ),
        "field_predictability":
            field_confidence,
        "field_divergence":
            _number(
                field_row.get(
                    "field_divergence",
                    0.0,
                )
            ),
        "field_curl":
            _number(
                field_row.get(
                    "field_curl",
                    0.0,
                )
            ),
        "field_strain":
            _number(
                field_row.get(
                    "field_strain_magnitude",
                    0.0,
                )
            ),
        "evolution_signal":
            evolution_signal,
        "estimated_bars_to_attractor":
            _number(
                evolution_row.get(
                    "estimated_bars_to_attractor",
                    0.0,
                )
            ),
        "trajectory_confidence":
            trajectory_confidence,
        "reasons":
            sorted(
                set(reasons)
            ),
    }

    payload[
        "decision_id"
    ] = decision_id(
        payload
    )

    return payload


def build_morphology_execution_decisions(
    *,
    latest_trajectories: pd.DataFrame,
    latest_evolution: pd.DataFrame,
    latest_field: pd.DataFrame,
    validated_discovery: pd.DataFrame,
    config: MorphologyExecutionConfig = (
        MorphologyExecutionConfig()
    ),
) -> pd.DataFrame:
    assets = sorted(
        set(
            latest_evolution.get(
                "asset",
                pd.Series(
                    dtype=str
                ),
            )
            .astype(str)
            .str.upper()
        )
        | set(
            validated_discovery.get(
                "asset",
                pd.Series(
                    dtype=str
                ),
            )
            .astype(str)
            .str.upper()
        )
    )

    if not assets:
        assets = [
            "BTC",
            "ETH",
            "SOL",
        ]

    field_row = (
        latest_field.iloc[0]
        if not latest_field.empty
        else pd.Series(dtype=object)
    )

    rows = []

    for asset in assets:
        evolution_rows = (
            latest_evolution[
                latest_evolution[
                    "asset"
                ].astype(str).str.upper().eq(
                    asset
                )
            ]
            if (
                not latest_evolution.empty
                and "asset"
                in latest_evolution.columns
            )
            else pd.DataFrame()
        )

        evolution_row = (
            evolution_rows.iloc[0]
            if not evolution_rows.empty
            else pd.Series(dtype=object)
        )

        trajectory_rows = (
            latest_trajectories[
                latest_trajectories[
                    "asset"
                ].astype(str).str.upper().eq(
                    asset
                )
            ]
            if (
                not latest_trajectories.empty
                and "asset"
                in latest_trajectories.columns
            )
            else pd.DataFrame()
        )

        trajectory_row = (
            trajectory_rows.sort_values(
                [
                    "trajectory_score",
                    "observation_count",
                ],
                ascending=[
                    False,
                    False,
                ],
                kind="stable",
            ).iloc[0]
            if not trajectory_rows.empty
            else None
        )

        rows.append(
            build_asset_decision(
                asset=asset,
                field_row=field_row,
                evolution_row=evolution_row,
                trajectory_row=trajectory_row,
                discovery=validated_discovery,
                config=config,
            )
        )

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "entry_ready",
                "confidence",
                "asset",
            ],
            ascending=[
                False,
                False,
                True,
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def write_morphology_execution_outputs(
    *,
    decisions: pd.DataFrame,
    config: MorphologyExecutionConfig,
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
        / "morphology_execution_decisions.csv"
    )

    json_path = (
        directory
        / "morphology_execution_decisions.json"
    )

    summary_path = (
        directory
        / "morphology_execution_summary.json"
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
            "atlas.morphology_execution_summary.v1",
        "config":
            asdict(config),
        "decision_count":
            int(len(decisions)),
        "entry_ready_count":
            int(
                decisions[
                    "entry_ready"
                ].astype(bool).sum()
            ) if not decisions.empty else 0,
        "research_only":
            True,
        "live_authorized":
            False,
        "decisions":
            decisions.to_dict(
                orient="records"
            ),
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
