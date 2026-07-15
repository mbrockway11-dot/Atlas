"""Morphology decision to portfolio-target adapter.

This module converts Morphology Execution Decision V1 outputs into proposed
portfolio targets for Atlas's existing intent, risk, approval, and execution
pipeline.

It does not:
- place orders;
- invoke an exchange;
- approve live trading;
- bypass the existing allocator or risk controls;
- maintain positions or balances.
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


@dataclass(frozen=True, slots=True)
class MorphologyPortfolioAdapterConfig:
    maximum_total_exposure: float = 0.10
    maximum_asset_exposure: float = 0.10
    maximum_positions: int = 1
    minimum_confidence: float = 0.70
    minimum_validated_uplift: float = 0.0
    confidence_power: float = 2.0
    include_cash_row: bool = True
    research_only: bool = True
    require_manual_approval: bool = True

    def __post_init__(self) -> None:
        for name in (
            "maximum_total_exposure",
            "maximum_asset_exposure",
            "minimum_confidence",
        ):
            value = float(getattr(self, name))

            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between zero and one."
                )

        if self.maximum_positions < 1:
            raise ValueError(
                "maximum_positions must be positive."
            )

        if (
            not math.isfinite(self.confidence_power)
            or self.confidence_power <= 0.0
        ):
            raise ValueError(
                "confidence_power must be positive."
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


def load_morphology_decisions(
    path: str | Path,
) -> pd.DataFrame:
    source = Path(path)

    if not source.exists():
        raise FileNotFoundError(
            f"Morphology decision file does not exist: {source}"
        )

    frame = pd.read_csv(
        source,
        low_memory=False,
    )

    required = {
        "decision_id",
        "timestamp",
        "asset",
        "action",
        "direction",
        "entry_ready",
        "confidence",
        "target_exposure",
        "research_only",
        "live_authorized",
        "validation_weighted_uplift",
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            "Morphology decisions are missing required columns: "
            f"{missing}"
        )

    frame = frame.copy()

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        utc=True,
        errors="coerce",
    )

    frame["asset"] = (
        frame["asset"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    frame["direction"] = (
        frame["direction"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    frame["action"] = (
        frame["action"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    for column in (
        "confidence",
        "target_exposure",
        "validation_weighted_uplift",
    ):
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        ).fillna(0.0)

    for column in (
        "entry_ready",
        "research_only",
        "live_authorized",
    ):
        frame[column] = frame[column].map(
            _boolean
        )

    return (
        frame.dropna(
            subset=[
                "timestamp",
                "asset",
            ]
        )
        .sort_values(
            [
                "timestamp",
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


def eligible_decisions(
    decisions: pd.DataFrame,
    *,
    config: MorphologyPortfolioAdapterConfig,
) -> pd.DataFrame:
    if decisions.empty:
        return decisions.copy()

    eligible = decisions[
        decisions["entry_ready"].astype(bool)
        & decisions["action"].eq("ENTER")
        & decisions["direction"].isin(
            ["LONG", "SHORT"]
        )
        & decisions["confidence"].ge(
            config.minimum_confidence
        )
        & decisions[
            "validation_weighted_uplift"
        ].gt(
            config.minimum_validated_uplift
        )
    ].copy()

    # The research decision engine must never self-authorize live activity.
    eligible = eligible[
        ~eligible[
            "live_authorized"
        ].astype(bool)
    ]

    return (
        eligible.sort_values(
            [
                "confidence",
                "validation_weighted_uplift",
                "asset",
            ],
            ascending=[
                False,
                False,
                True,
            ],
            kind="stable",
        )
        .drop_duplicates(
            subset=["asset"],
            keep="first",
        )
        .head(
            config.maximum_positions
        )
        .reset_index(drop=True)
    )


def allocation_scores(
    decisions: pd.DataFrame,
    *,
    config: MorphologyPortfolioAdapterConfig,
) -> pd.Series:
    if decisions.empty:
        return pd.Series(
            dtype=float
        )

    confidence = decisions[
        "confidence"
    ].clip(
        lower=0.0,
        upper=1.0,
    )

    uplift = decisions[
        "validation_weighted_uplift"
    ].clip(
        lower=0.0,
    )

    uplift_scale = max(
        float(uplift.max()),
        1e-12,
    )

    normalized_uplift = (
        uplift / uplift_scale
    )

    raw = (
        confidence.pow(
            config.confidence_power
        )
        * (
            0.75
            + 0.25
            * normalized_uplift
        )
    )

    if float(raw.sum()) <= 0.0:
        return pd.Series(
            0.0,
            index=decisions.index,
        )

    return raw / float(raw.sum())


def portfolio_batch_id(
    rows: list[dict[str, Any]],
) -> str:
    canonical = json.dumps(
        rows,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    digest = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()[:24]

    return f"MORPH-PORT-{digest}"


def build_morphology_portfolio_targets(
    decisions: pd.DataFrame,
    *,
    config: MorphologyPortfolioAdapterConfig = (
        MorphologyPortfolioAdapterConfig()
    ),
) -> pd.DataFrame:
    selected = eligible_decisions(
        decisions,
        config=config,
    )

    rows: list[dict[str, Any]] = []

    if not selected.empty:
        weights = allocation_scores(
            selected,
            config=config,
        )

        for index, decision in selected.iterrows():
            proposed_exposure = min(
                config.maximum_asset_exposure,
                config.maximum_total_exposure
                * float(weights.loc[index]),
                max(
                    _number(
                        decision.get(
                            "target_exposure",
                            0.0,
                        )
                    ),
                    0.0,
                ),
            )

            direction = str(
                decision["direction"]
            ).upper()

            signed_exposure = (
                -proposed_exposure
                if direction == "SHORT"
                else proposed_exposure
            )

            rows.append({
                "schema_version":
                    "atlas.morphology_portfolio_target.v1",
                "timestamp":
                    str(
                        decision["timestamp"]
                    ),
                "asset":
                    str(
                        decision["asset"]
                    ),
                "direction":
                    direction,
                "target_weight":
                    signed_exposure,
                "target_exposure":
                    abs(
                        signed_exposure
                    ),
                "allocation_rank":
                    int(index + 1),
                "confidence":
                    _number(
                        decision["confidence"]
                    ),
                "validated_uplift":
                    _number(
                        decision[
                            "validation_weighted_uplift"
                        ]
                    ),
                "source_decision_id":
                    str(
                        decision["decision_id"]
                    ),
                "source_engine":
                    "MORPHOLOGY_EXECUTION_DECISION_V1",
                "intent_state":
                    "PROPOSED",
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
            })

    gross_exposure = sum(
        abs(
            _number(
                row["target_weight"]
            )
        )
        for row in rows
    )

    if gross_exposure > (
        config.maximum_total_exposure
        + 1e-12
    ):
        raise ValueError(
            "Generated portfolio exceeds maximum total exposure."
        )

    if config.include_cash_row:
        latest_timestamp = (
            str(
                decisions[
                    "timestamp"
                ].max()
            )
            if not decisions.empty
            else ""
        )

        rows.append({
            "schema_version":
                "atlas.morphology_portfolio_target.v1",
            "timestamp":
                latest_timestamp,
            "asset":
                "CASH",
            "direction":
                "FLAT",
            "target_weight":
                max(
                    0.0,
                    1.0 - gross_exposure,
                ),
            "target_exposure":
                0.0,
            "allocation_rank":
                0,
            "confidence":
                1.0,
            "validated_uplift":
                0.0,
            "source_decision_id":
                "",
            "source_engine":
                "MORPHOLOGY_PORTFOLIO_ADAPTER_V1",
            "intent_state":
                "PROPOSED",
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
        })

    batch_id = portfolio_batch_id(
        rows
    )

    for row in rows:
        row[
            "portfolio_batch_id"
        ] = batch_id

    return pd.DataFrame(rows)


def write_morphology_portfolio_outputs(
    *,
    targets: pd.DataFrame,
    config: MorphologyPortfolioAdapterConfig,
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
        / "morphology_portfolio_targets.csv"
    )

    json_path = (
        directory
        / "morphology_portfolio_targets.json"
    )

    summary_path = (
        directory
        / "morphology_portfolio_summary.json"
    )

    targets.to_csv(
        csv_path,
        index=False,
    )

    json_path.write_text(
        json.dumps(
            targets.to_dict(
                orient="records"
            ),
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    asset_targets = targets[
        ~targets[
            "asset"
        ].eq("CASH")
    ] if not targets.empty else targets

    summary = {
        "schema_version":
            "atlas.morphology_portfolio_summary.v1",
        "config":
            asdict(config),
        "target_count":
            int(len(asset_targets)),
        "gross_target_exposure":
            float(
                asset_targets[
                    "target_weight"
                ].abs().sum()
            ) if not asset_targets.empty else 0.0,
        "research_only":
            True,
        "live_authorized":
            False,
        "order_submission_allowed":
            False,
        "targets":
            targets.to_dict(
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
