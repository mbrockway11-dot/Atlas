"""Multi-layer morphology expression discovery.

Expression Engine V3 fuses leakage-safe field scores with evolution and
trajectory observations, engineers cross-layer predicates, and discovers
two- and three-factor interactions on early folds before evaluating them on
later unseen folds.

The engine reuses Atlas's existing:
- cluster-matched controls;
- non-overlapping event selection;
- transaction-cost adjustment;
- chronological discovery/validation split;
- multiple-testing correction.

Research only. It does not emit portfolio intents or place orders.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from atlas.investment.morphology_intelligence.discovery import (
    MorphologyDiscoveryConfig,
    apply_candidate,
    candidate_record,
    run_discovery_evaluation,
    split_discovery_validation_folds,
    summarize_discovery,
)


FIELD_BOOLEAN_FEATURES = (
    "field_high_predictability",
    "field_high_expansion",
    "field_high_contraction",
    "field_high_rotation",
    "field_high_strain",
    "field_combined_opportunity",
)

EVOLUTION_BOOLEAN_FEATURES = (
    "expression_approaching_attractor",
    "expression_strong_approach",
    "expression_positive_closing_efficiency",
    "expression_near_attractor",
    "expression_short_attractor_eta",
    "expression_receding",
)

TRAJECTORY_BOOLEAN_FEATURES = (
    "expression_trajectory_enter",
    "expression_trajectory_positive",
    "expression_trajectory_high_confidence",
    "expression_trajectory_progressive",
    "expression_trajectory_oscillating",
)

MOTION_BOOLEAN_FEATURES = (
    "expression_motion_accelerating",
    "expression_motion_flowing",
    "expression_motion_turning",
    "expression_high_directional_stability",
)

ALL_EXPRESSION_FEATURES = (
    FIELD_BOOLEAN_FEATURES
    + EVOLUTION_BOOLEAN_FEATURES
    + TRAJECTORY_BOOLEAN_FEATURES
    + MOTION_BOOLEAN_FEATURES
)


@dataclass(frozen=True, slots=True)
class MorphologyExpressionConfig:
    horizon_bars: int = 16
    transaction_cost_bps: float = 8.0
    non_overlap_bars: int = 16
    discovery_fraction: float = 0.60

    minimum_raw_candidate_rows: int = 500
    minimum_condition_observations: int = 10
    minimum_control_observations: int = 10
    minimum_cluster_observations: int = 20
    minimum_discovery_folds: int = 6
    minimum_validation_folds: int = 4

    minimum_discovery_uplift_rate: float = 0.60
    minimum_validation_uplift_rate: float = 0.60
    multiple_testing_alpha: float = 0.10

    maximum_pair_candidates: int = 120
    maximum_triple_candidates: int = 120

    near_attractor_distance: float = 1.0
    short_attractor_eta: float = 32.0
    high_directional_stability: float = 0.60
    high_trajectory_score_quantile: float = 0.75

    def discovery_config(
        self,
    ) -> MorphologyDiscoveryConfig:
        return MorphologyDiscoveryConfig(
            horizon_bars=self.horizon_bars,
            transaction_cost_bps=self.transaction_cost_bps,
            non_overlap_bars=self.non_overlap_bars,
            discovery_fraction=self.discovery_fraction,
            minimum_raw_candidate_rows=(
                self.minimum_raw_candidate_rows
            ),
            minimum_condition_observations=(
                self.minimum_condition_observations
            ),
            minimum_control_observations=(
                self.minimum_control_observations
            ),
            minimum_cluster_observations=(
                self.minimum_cluster_observations
            ),
            minimum_discovery_folds=(
                self.minimum_discovery_folds
            ),
            minimum_validation_folds=(
                self.minimum_validation_folds
            ),
            minimum_discovery_uplift_rate=(
                self.minimum_discovery_uplift_rate
            ),
            minimum_validation_uplift_rate=(
                self.minimum_validation_uplift_rate
            ),
            maximum_pair_candidates=(
                self.maximum_pair_candidates
            ),
            multiple_testing_alpha=(
                self.multiple_testing_alpha
            ),
        )


def _boolean_series(
    frame: pd.DataFrame,
    column: str,
) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(
            False,
            index=frame.index,
            dtype=bool,
        )

    values = frame[column]

    if pd.api.types.is_bool_dtype(values):
        return values.fillna(False)

    return (
        values.astype(str)
        .str.strip()
        .str.lower()
        .map({
            "true": True,
            "false": False,
            "1": True,
            "0": False,
            "yes": True,
            "no": False,
        })
        .fillna(False)
        .astype(bool)
    )


def _numeric(
    frame: pd.DataFrame,
    column: str,
    *,
    default: float = 0.0,
) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(
            default,
            index=frame.index,
            dtype=float,
        )

    return pd.to_numeric(
        frame[column],
        errors="coerce",
    ).fillna(default)


def _normalize_timestamp(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    result = frame.copy()

    timestamp_column = next(
        (
            column
            for column in (
                "timestamp",
                "window_end",
                "entry_timestamp",
                "entry_time",
            )
            if column in result.columns
        ),
        None,
    )

    if timestamp_column is None:
        raise ValueError(
            "Input frame has no supported timestamp column."
        )

    if timestamp_column != "timestamp":
        result = result.rename(
            columns={
                timestamp_column: "timestamp",
            }
        )

    result["timestamp"] = pd.to_datetime(
        result["timestamp"],
        utc=True,
        errors="coerce",
    )

    return result.dropna(
        subset=["timestamp"]
    ).reset_index(drop=True)


def load_expression_scores(
    path: str | Path,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    required = {
        "timestamp",
        "fold_id",
        "morphology_cluster_id",
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            f"Field scores missing columns: {missing}"
        )

    frame = _normalize_timestamp(frame)

    frame["fold_id"] = pd.to_numeric(
        frame["fold_id"],
        errors="coerce",
    )

    frame["morphology_cluster_id"] = pd.to_numeric(
        frame["morphology_cluster_id"],
        errors="coerce",
    )

    for column in FIELD_BOOLEAN_FEATURES:
        frame[column] = _boolean_series(
            frame,
            column,
        )

    return (
        frame.dropna(
            subset=[
                "fold_id",
                "morphology_cluster_id",
            ]
        )
        .assign(
            fold_id=lambda value:
                value["fold_id"].astype(int),
            morphology_cluster_id=lambda value:
                value[
                    "morphology_cluster_id"
                ].astype(int),
        )
        .sort_values(
            [
                "fold_id",
                "timestamp",
            ],
            kind="stable",
        )
        .drop_duplicates(
            subset=[
                "fold_id",
                "timestamp",
            ],
            keep="last",
        )
        .reset_index(drop=True)
    )


def load_expression_evolution(
    path: str | Path,
) -> pd.DataFrame:
    frame = _normalize_timestamp(
        pd.read_csv(
            path,
            low_memory=False,
        )
    )

    if "asset" not in frame.columns:
        raise ValueError(
            "Evolution observations require asset."
        )

    frame["asset"] = (
        frame["asset"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

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
            ],
            keep="first",
        )
        .reset_index(drop=True)
    )


def load_expression_trajectories(
    path: str | Path,
) -> pd.DataFrame:
    frame = _normalize_timestamp(
        pd.read_csv(
            path,
            low_memory=False,
        )
    )

    if "asset" not in frame.columns:
        raise ValueError(
            "Trajectory observations require asset."
        )

    frame["asset"] = (
        frame["asset"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    sort_columns = [
        "timestamp",
        "asset",
    ]

    if "trajectory_score" in frame.columns:
        frame["trajectory_score"] = pd.to_numeric(
            frame["trajectory_score"],
            errors="coerce",
        ).fillna(0.0)

        frame = frame.sort_values(
            sort_columns
            + ["trajectory_score"],
            ascending=[
                True,
                True,
                False,
            ],
            kind="stable",
        )
    else:
        frame = frame.sort_values(
            sort_columns,
            kind="stable",
        )

    return (
        frame.drop_duplicates(
            subset=[
                "timestamp",
                "asset",
            ],
            keep="first",
        )
        .reset_index(drop=True)
    )


def engineer_expression_features(
    frame: pd.DataFrame,
    *,
    config: MorphologyExpressionConfig,
) -> pd.DataFrame:
    result = frame.copy()

    evolution_signal = (
        result.get(
            "evolution_signal",
            pd.Series(
                "",
                index=result.index,
            ),
        )
        .astype(str)
        .str.upper()
    )

    result[
        "expression_approaching_attractor"
    ] = evolution_signal.isin({
        "STRONG_APPROACH",
        "APPROACH",
        "WEAK_APPROACH",
    })

    result[
        "expression_strong_approach"
    ] = evolution_signal.eq(
        "STRONG_APPROACH"
    )

    result[
        "expression_receding"
    ] = evolution_signal.isin({
        "RECEDING",
        "WEAK_RECESSION",
    })

    result[
        "expression_positive_closing_efficiency"
    ] = _numeric(
        result,
        "attractor_closing_efficiency",
    ).gt(0.0)

    result[
        "expression_near_attractor"
    ] = _numeric(
        result,
        "distance_to_attractor",
        default=np.inf,
    ).le(
        config.near_attractor_distance
    )

    result[
        "expression_short_attractor_eta"
    ] = _numeric(
        result,
        "estimated_bars_to_attractor",
        default=np.inf,
    ).le(
        config.short_attractor_eta
    )

    trajectory_action = (
        result.get(
            "recommended_action",
            pd.Series(
                "",
                index=result.index,
            ),
        )
        .astype(str)
        .str.upper()
    )

    result[
        "expression_trajectory_enter"
    ] = trajectory_action.eq("ENTER")

    trajectory_score = _numeric(
        result,
        "trajectory_score",
    )

    result[
        "expression_trajectory_positive"
    ] = trajectory_score.gt(0.0)

    if trajectory_score.notna().any():
        threshold = float(
            trajectory_score.quantile(
                config.high_trajectory_score_quantile
            )
        )
    else:
        threshold = 0.0

    result[
        "expression_trajectory_high_confidence"
    ] = trajectory_score.ge(
        threshold
    ) & trajectory_score.gt(0.0)

    trajectory_shape = (
        result.get(
            "trajectory_shape",
            pd.Series(
                "",
                index=result.index,
            ),
        )
        .astype(str)
        .str.upper()
    )

    result[
        "expression_trajectory_progressive"
    ] = trajectory_shape.eq(
        "PROGRESSIVE"
    )

    result[
        "expression_trajectory_oscillating"
    ] = trajectory_shape.eq(
        "OSCILLATING"
    )

    motion_state = (
        result.get(
            "morphology_motion_state",
            pd.Series(
                "",
                index=result.index,
            ),
        )
        .astype(str)
        .str.upper()
    )

    result[
        "expression_motion_accelerating"
    ] = motion_state.eq(
        "ACCELERATING"
    )

    result[
        "expression_motion_flowing"
    ] = motion_state.eq(
        "FLOWING"
    )

    result[
        "expression_motion_turning"
    ] = motion_state.eq(
        "TURNING"
    )

    result[
        "expression_high_directional_stability"
    ] = _numeric(
        result,
        "morphology_directional_stability",
    ).ge(
        config.high_directional_stability
    )

    for column in ALL_EXPRESSION_FEATURES:
        result[column] = _boolean_series(
            result,
            column,
        )

    return result


def fuse_expression_inputs(
    *,
    scores: pd.DataFrame,
    evolution: pd.DataFrame,
    trajectories: pd.DataFrame,
    outcomes: pd.DataFrame,
    config: MorphologyExpressionConfig,
) -> pd.DataFrame:
    joined = outcomes.merge(
        scores,
        on=[
            "timestamp",
            "morphology_cluster_id",
        ],
        how="inner",
        validate="many_to_one",
        suffixes=(
            "",
            "_field",
        ),
    )

    evolution_columns = [
        column
        for column in evolution.columns
        if column not in {
            "morphology_cluster_id",
            "morphology_cluster",
        }
    ]

    joined = joined.merge(
        evolution[
            evolution_columns
        ],
        on=[
            "timestamp",
            "asset",
        ],
        how="left",
        validate="many_to_one",
        suffixes=(
            "",
            "_evolution",
        ),
    )

    trajectory_columns = [
        column
        for column in trajectories.columns
        if column not in {
            "morphology_cluster_id",
            "morphology_cluster",
        }
    ]

    joined = joined.merge(
        trajectories[
            trajectory_columns
        ],
        on=[
            "timestamp",
            "asset",
        ],
        how="left",
        validate="many_to_one",
        suffixes=(
            "",
            "_trajectory",
        ),
    )

    return engineer_expression_features(
        joined,
        config=config,
    )


def _expression_id(
    features: Iterable[str],
) -> str:
    expression = " AND ".join(
        sorted(features)
    )

    digest = hashlib.sha256(
        expression.encode("utf-8")
    ).hexdigest()[:16]

    return f"EXPR-V3-{digest}"


def _catalog_record(
    features: tuple[str, ...],
) -> dict[str, Any]:
    expression = " AND ".join(
        f"{feature} == True"
        for feature in features
    )

    record = {
        "candidate_id":
            _expression_id(features),
        "candidate_kind":
            (
                "single"
                if len(features) == 1
                else (
                    "pair"
                    if len(features) == 2
                    else "triple"
                )
            ),
        "expression":
            expression,
        "feature_a":
            features[0],
        "operator_a":
            "IS_TRUE",
        "value_a":
            "True",
        "feature_b":
            (
                features[1]
                if len(features) >= 2
                else ""
            ),
        "operator_b":
            (
                "IS_TRUE"
                if len(features) >= 2
                else ""
            ),
        "value_b":
            (
                "True"
                if len(features) >= 2
                else ""
            ),
        "feature_c":
            (
                features[2]
                if len(features) >= 3
                else ""
            ),
    }

    return record


def apply_expression_candidate(
    frame: pd.DataFrame,
    candidate: dict[str, Any],
) -> pd.Series:
    mask = apply_candidate(
        frame,
        candidate,
    )

    feature_c = str(
        candidate.get(
            "feature_c",
            "",
        )
    )

    if feature_c:
        mask &= _boolean_series(
            frame,
            feature_c,
        )

    return mask


def build_expression_catalog(
    frame: pd.DataFrame,
    *,
    config: MorphologyExpressionConfig,
) -> pd.DataFrame:
    available = [
        feature
        for feature in ALL_EXPRESSION_FEATURES
        if (
            feature in frame.columns
            and _boolean_series(
                frame,
                feature,
            ).any()
            and (
                ~_boolean_series(
                    frame,
                    feature,
                )
            ).any()
        )
    ]

    rows: list[dict[str, Any]] = []

    for feature in available:
        rows.append(
            _catalog_record(
                (feature,)
            )
        )

    pair_count = 0

    for left_index, left in enumerate(
        available
    ):
        for right in available[
            left_index + 1:
        ]:
            if (
                pair_count
                >= config.maximum_pair_candidates
            ):
                break

            rows.append(
                _catalog_record(
                    (
                        left,
                        right,
                    )
                )
            )

            pair_count += 1

        if (
            pair_count
            >= config.maximum_pair_candidates
        ):
            break

    triple_count = 0

    field_features = [
        feature
        for feature in available
        if feature.startswith(
            "field_"
        )
    ]

    evolution_features = [
        feature
        for feature in available
        if feature
        in EVOLUTION_BOOLEAN_FEATURES
    ]

    trajectory_features = [
        feature
        for feature in available
        if feature
        in TRAJECTORY_BOOLEAN_FEATURES
    ]

    for field_feature in field_features:
        for evolution_feature in (
            evolution_features
        ):
            for trajectory_feature in (
                trajectory_features
            ):
                if (
                    triple_count
                    >= config.maximum_triple_candidates
                ):
                    break

                rows.append(
                    _catalog_record(
                        (
                            field_feature,
                            evolution_feature,
                            trajectory_feature,
                        )
                    )
                )

                triple_count += 1

            if (
                triple_count
                >= config.maximum_triple_candidates
            ):
                break

        if (
            triple_count
            >= config.maximum_triple_candidates
        ):
            break

    catalog = pd.DataFrame(rows)

    raw_counts = []

    for candidate in catalog.to_dict(
        orient="records"
    ):
        raw_counts.append(
            int(
                apply_expression_candidate(
                    frame,
                    candidate,
                ).sum()
            )
        )

    catalog[
        "raw_observation_count"
    ] = raw_counts

    return (
        catalog[
            catalog[
                "raw_observation_count"
            ].ge(
                config.minimum_raw_candidate_rows
            )
        ]
        .drop_duplicates(
            subset=["candidate_id"]
        )
        .sort_values(
            [
                "candidate_kind",
                "raw_observation_count",
            ],
            ascending=[
                True,
                False,
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def evaluate_expression_catalog(
    frame: pd.DataFrame,
    *,
    catalog: pd.DataFrame,
    config: MorphologyExpressionConfig,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    tuple[int, ...],
    tuple[int, ...],
]:
    discovery_folds, validation_folds = (
        split_discovery_validation_folds(
            frame["fold_id"],
            discovery_fraction=(
                config.discovery_fraction
            ),
        )
    )

    # Discovery V2 understands two clauses natively. Triple clauses are
    # materialized into deterministic synthetic booleans.
    evaluation_frame = frame.copy()
    evaluation_catalog = catalog.copy()

    for index, candidate in (
        evaluation_catalog.iterrows()
    ):
        feature_c = str(
            candidate.get(
                "feature_c",
                "",
            )
        )

        if not feature_c:
            continue

        synthetic_column = (
            "expression_candidate_"
            + str(
                candidate[
                    "candidate_id"
                ]
            ).lower().replace(
                "-",
                "_",
            )
        )

        evaluation_frame[
            synthetic_column
        ] = apply_expression_candidate(
            evaluation_frame,
            candidate.to_dict(),
        )

        evaluation_catalog.loc[
            index,
            "feature_a",
        ] = synthetic_column

        evaluation_catalog.loc[
            index,
            "operator_a",
        ] = "IS_TRUE"

        evaluation_catalog.loc[
            index,
            "value_a",
        ] = "True"

        evaluation_catalog.loc[
            index,
            "feature_b",
        ] = ""

        evaluation_catalog.loc[
            index,
            "operator_b",
        ] = ""

        evaluation_catalog.loc[
            index,
            "value_b",
        ] = ""

    evaluations = run_discovery_evaluation(
        evaluation_frame,
        catalog=evaluation_catalog,
        discovery_folds=discovery_folds,
        validation_folds=validation_folds,
        config=config.discovery_config(),
    )

    summary = summarize_discovery(
        evaluations,
        config=config.discovery_config(),
    )

    return (
        evaluations,
        summary,
        discovery_folds,
        validation_folds,
    )


def write_expression_outputs(
    *,
    fused: pd.DataFrame,
    catalog: pd.DataFrame,
    evaluations: pd.DataFrame,
    summary: pd.DataFrame,
    discovery_folds: tuple[int, ...],
    validation_folds: tuple[int, ...],
    config: MorphologyExpressionConfig,
    output_dir: str | Path,
) -> dict[str, Path]:
    directory = Path(
        output_dir
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    outputs = {
        "features":
            directory
            / "morphology_expression_features.csv",
        "catalog":
            directory
            / "morphology_expression_catalog.csv",
        "folds":
            directory
            / "morphology_expression_folds.csv",
        "summary":
            directory
            / "morphology_expression_summary.csv",
        "validated":
            directory
            / "morphology_expression_validated.csv",
        "report":
            directory
            / "morphology_expression_report.json",
    }

    feature_columns = [
        "timestamp",
        "fold_id",
        "asset",
        "morphology_cluster_id",
        "field_supported",
        *[
            feature
            for feature
            in ALL_EXPRESSION_FEATURES
            if feature in fused.columns
        ],
    ]

    fused[
        feature_columns
    ].to_csv(
        outputs["features"],
        index=False,
    )

    catalog.to_csv(
        outputs["catalog"],
        index=False,
    )

    evaluations.to_csv(
        outputs["folds"],
        index=False,
    )

    summary.to_csv(
        outputs["summary"],
        index=False,
    )

    validated = (
        summary[
            summary[
                "validated"
            ].astype(bool)
        ]
        if not summary.empty
        else pd.DataFrame()
    )

    validated.to_csv(
        outputs["validated"],
        index=False,
    )

    report = {
        "schema_version":
            "atlas.morphology_expression.v3",
        "config":
            asdict(config),
        "fused_rows":
            int(len(fused)),
        "catalog_candidates":
            int(len(catalog)),
        "single_candidates":
            int(
                catalog[
                    "candidate_kind"
                ].eq("single").sum()
            ) if not catalog.empty else 0,
        "pair_candidates":
            int(
                catalog[
                    "candidate_kind"
                ].eq("pair").sum()
            ) if not catalog.empty else 0,
        "triple_candidates":
            int(
                catalog[
                    "candidate_kind"
                ].eq("triple").sum()
            ) if not catalog.empty else 0,
        "discovery_folds":
            list(discovery_folds),
        "validation_folds":
            list(validation_folds),
        "evaluation_rows":
            int(len(evaluations)),
        "discovered_count":
            int(
                summary[
                    "discovered"
                ].astype(bool).sum()
            ) if not summary.empty else 0,
        "validated_count":
            int(len(validated)),
        "validated_expressions":
            (
                validated.to_dict(
                    orient="records"
                )
                if not validated.empty
                else []
            ),
    }

    outputs["report"].write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    return outputs
