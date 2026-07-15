"""Automated morphology-condition discovery with held-out validation.

The engine generates hypotheses from leakage-safe field scores, discovers
promising candidates on earlier walk-forward folds, and validates only those
candidates on later folds.

Controls:
- chronological discovery/validation split;
- same-fold and same-cluster controls;
- independently non-overlapping condition and control events;
- transaction costs;
- minimum observation and fold requirements;
- exact binomial sign tests;
- Benjamini-Hochberg multiple-testing correction.

Research only. No portfolio intents or orders are produced.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from atlas.investment.morphology_intelligence.field_incremental_value import (
    benjamini_hochberg,
    cluster_weighted_uplift,
    load_incremental_outcomes,
    load_incremental_scores,
    infer_base_bar_interval,
    sample_metrics,
    select_non_overlapping,
)


BASE_BOOLEAN_FEATURES = (
    "field_high_predictability",
    "field_high_expansion",
    "field_high_contraction",
    "field_high_rotation",
    "field_high_strain",
    "field_combined_opportunity",
)


@dataclass(frozen=True, slots=True)
class MorphologyDiscoveryConfig:
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
    minimum_weighted_uplift: float = 0.0
    maximum_pair_candidates: int = 30
    multiple_testing_alpha: float = 0.10

    def __post_init__(self) -> None:
        integer_fields = (
            "horizon_bars",
            "non_overlap_bars",
            "minimum_raw_candidate_rows",
            "minimum_condition_observations",
            "minimum_control_observations",
            "minimum_cluster_observations",
            "minimum_discovery_folds",
            "minimum_validation_folds",
            "maximum_pair_candidates",
        )

        for name in integer_fields:
            if int(getattr(self, name)) < 1:
                raise ValueError(
                    f"{name} must be positive."
                )

        if (
            not math.isfinite(self.transaction_cost_bps)
            or self.transaction_cost_bps < 0.0
        ):
            raise ValueError(
                "transaction_cost_bps must be nonnegative."
            )

        for name in (
            "discovery_fraction",
            "minimum_discovery_uplift_rate",
            "minimum_validation_uplift_rate",
            "multiple_testing_alpha",
        ):
            value = float(getattr(self, name))

            if not 0.0 < value < 1.0:
                raise ValueError(
                    f"{name} must be between zero and one."
                )


def boolean_series(
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

    if pd.api.types.is_bool_dtype(
        values
    ):
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
        })
        .fillna(False)
        .astype(bool)
    )


def candidate_identity(
    *,
    kind: str,
    expression: str,
) -> str:
    import hashlib

    digest = hashlib.sha256(
        f"{kind}|{expression}".encode(
            "utf-8"
        )
    ).hexdigest()[:16]

    return (
        f"DISC-{kind.upper()}-{digest}"
    )


def candidate_record(
    *,
    kind: str,
    expression: str,
    feature_a: str = "",
    operator_a: str = "",
    value_a: str = "",
    feature_b: str = "",
    operator_b: str = "",
    value_b: str = "",
) -> dict[str, Any]:
    return {
        "candidate_id":
            candidate_identity(
                kind=kind,
                expression=expression,
            ),
        "candidate_kind":
            kind,
        "expression":
            expression,
        "feature_a":
            feature_a,
        "operator_a":
            operator_a,
        "value_a":
            value_a,
        "feature_b":
            feature_b,
        "operator_b":
            operator_b,
        "value_b":
            value_b,
    }


def build_candidate_catalog(
    scores: pd.DataFrame,
    *,
    config: MorphologyDiscoveryConfig,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    available_booleans = [
        column
        for column in BASE_BOOLEAN_FEATURES
        if column in scores.columns
    ]

    for column in available_booleans:
        positive_expression = (
            f"{column} == True"
        )

        rows.append(
            candidate_record(
                kind="boolean",
                expression=positive_expression,
                feature_a=column,
                operator_a="IS_TRUE",
                value_a="True",
            )
        )

        negative_expression = (
            f"{column} == False"
        )

        rows.append(
            candidate_record(
                kind="boolean",
                expression=negative_expression,
                feature_a=column,
                operator_a="IS_FALSE",
                value_a="False",
            )
        )

    pair_count = 0

    for left_index, left in enumerate(
        available_booleans
    ):
        for right in available_booleans[
            left_index + 1:
        ]:
            if (
                pair_count
                >= config.maximum_pair_candidates
            ):
                break

            expression = (
                f"{left} == True AND "
                f"{right} == True"
            )

            rows.append(
                candidate_record(
                    kind="conjunction",
                    expression=expression,
                    feature_a=left,
                    operator_a="IS_TRUE",
                    value_a="True",
                    feature_b=right,
                    operator_b="IS_TRUE",
                    value_b="True",
                )
            )

            pair_count += 1

        if (
            pair_count
            >= config.maximum_pair_candidates
        ):
            break

    categorical_features = (
        "field_validation_state",
        "field_flow_class",
        "morphology_motion_state",
        "evolution_signal",
    )

    for feature in categorical_features:
        if feature not in scores.columns:
            continue

        counts = (
            scores[feature]
            .astype(str)
            .value_counts()
        )

        for value, count in counts.items():
            if (
                int(count)
                < config.minimum_raw_candidate_rows
            ):
                continue

            if value in {
                "",
                "nan",
                "None",
                "OUTSIDE_FIELD",
                "UNCLASSIFIED",
            }:
                continue

            expression = (
                f"{feature} == {value}"
            )

            rows.append(
                candidate_record(
                    kind="categorical",
                    expression=expression,
                    feature_a=feature,
                    operator_a="EQUALS",
                    value_a=str(value),
                )
            )

    catalog = (
        pd.DataFrame(rows)
        .drop_duplicates(
            subset=["candidate_id"]
        )
        .reset_index(drop=True)
    )

    raw_counts = []

    for candidate in catalog.to_dict(
        orient="records"
    ):
        mask = apply_candidate(
            scores,
            candidate,
        )

        raw_counts.append(
            int(mask.sum())
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
        .sort_values(
            [
                "candidate_kind",
                "expression",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def evaluate_clause(
    frame: pd.DataFrame,
    *,
    feature: str,
    operator: str,
    value: str,
) -> pd.Series:
    if not feature:
        return pd.Series(
            True,
            index=frame.index,
            dtype=bool,
        )

    if feature not in frame.columns:
        return pd.Series(
            False,
            index=frame.index,
            dtype=bool,
        )

    if operator == "IS_TRUE":
        return boolean_series(
            frame,
            feature,
        )

    if operator == "IS_FALSE":
        return ~boolean_series(
            frame,
            feature,
        )

    if operator == "EQUALS":
        return (
            frame[feature]
            .astype(str)
            .eq(str(value))
        )

    raise ValueError(
        f"Unsupported candidate operator: {operator}"
    )


def apply_candidate(
    frame: pd.DataFrame,
    candidate: dict[str, Any],
) -> pd.Series:
    left = evaluate_clause(
        frame,
        feature=str(
            candidate.get(
                "feature_a",
                "",
            )
        ),
        operator=str(
            candidate.get(
                "operator_a",
                "",
            )
        ),
        value=str(
            candidate.get(
                "value_a",
                "",
            )
        ),
    )

    feature_b = str(
        candidate.get(
            "feature_b",
            "",
        )
    )

    if not feature_b:
        return left.fillna(False)

    right = evaluate_clause(
        frame,
        feature=feature_b,
        operator=str(
            candidate.get(
                "operator_b",
                "",
            )
        ),
        value=str(
            candidate.get(
                "value_b",
                "",
            )
        ),
    )

    return (
        left.fillna(False)
        & right.fillna(False)
    )


def split_discovery_validation_folds(
    fold_ids: pd.Series,
    *,
    discovery_fraction: float,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    ordered = tuple(
        sorted(
            set(
                int(value)
                for value in fold_ids
            )
        )
    )

    if len(ordered) < 2:
        raise ValueError(
            "At least two folds are required."
        )

    split_index = int(
        math.floor(
            len(ordered)
            * discovery_fraction
        )
    )

    split_index = max(
        1,
        min(
            split_index,
            len(ordered) - 1,
        ),
    )

    return (
        ordered[:split_index],
        ordered[split_index:],
    )


def matched_non_overlapping_samples(
    frame: pd.DataFrame,
    *,
    candidate_mask: pd.Series,
    config: MorphologyDiscoveryConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    supported = frame[
        boolean_series(
            frame,
            "field_supported",
        )
    ].copy()

    mask = candidate_mask.reindex(
        supported.index,
        fill_value=False,
    )

    raw_condition = supported[
        mask
    ].copy()

    raw_control = supported[
        ~mask
    ].copy()

    base_bar_interval = infer_base_bar_interval(
        supported
    )

    condition = (
        select_non_overlapping(
            raw_condition,
            bars=config.non_overlap_bars,
            bar_interval=base_bar_interval,
        )
    )

    control = (
        select_non_overlapping(
            raw_control,
            bars=config.non_overlap_bars,
            bar_interval=base_bar_interval,
        )
    )

    condition_counts = (
        condition.groupby(
            "morphology_cluster_id",
            observed=True,
        )
        .size()
    )

    control_counts = (
        control.groupby(
            "morphology_cluster_id",
            observed=True,
        )
        .size()
    )

    shared_clusters = (
        set(condition_counts.index)
        & set(control_counts.index)
    )

    valid_clusters = [
        int(cluster_id)
        for cluster_id in shared_clusters
        if (
            int(
                condition_counts.loc[
                    cluster_id
                ]
            )
            >= config.minimum_condition_observations
            and int(
                control_counts.loc[
                    cluster_id
                ]
            )
            >= config.minimum_control_observations
            and (
                int(
                    condition_counts.loc[
                        cluster_id
                    ]
                )
                + int(
                    control_counts.loc[
                        cluster_id
                    ]
                )
            )
            >= config.minimum_cluster_observations
        )
    ]

    return (
        condition[
            condition[
                "morphology_cluster_id"
            ].isin(valid_clusters)
        ].reset_index(drop=True),
        control[
            control[
                "morphology_cluster_id"
            ].isin(valid_clusters)
        ].reset_index(drop=True),
    )


def incremental_config_adapter(
    config: MorphologyDiscoveryConfig,
) -> Any:
    from atlas.investment.morphology_intelligence.field_incremental_value import (
        FieldIncrementalValueConfig,
    )

    return FieldIncrementalValueConfig(
        horizon_bars=config.horizon_bars,
        transaction_cost_bps=(
            config.transaction_cost_bps
        ),
        minimum_condition_observations=(
            config.minimum_condition_observations
        ),
        minimum_control_observations=(
            config.minimum_control_observations
        ),
        minimum_cluster_observations=(
            config.minimum_cluster_observations
        ),
        minimum_valid_folds=(
            config.minimum_validation_folds
        ),
        non_overlap_bars=(
            config.non_overlap_bars
        ),
        bootstrap_iterations=10,
        permutation_iterations=10,
    )


def evaluate_candidate_fold(
    frame: pd.DataFrame,
    *,
    candidate: dict[str, Any],
    direction: str,
    config: MorphologyDiscoveryConfig,
) -> dict[str, Any] | None:
    mask = apply_candidate(
        frame,
        candidate,
    )

    condition, control = (
        matched_non_overlapping_samples(
            frame,
            candidate_mask=mask,
            config=config,
        )
    )

    if (
        len(condition)
        < config.minimum_condition_observations
        or len(control)
        < config.minimum_control_observations
    ):
        return None

    incremental_config = (
        incremental_config_adapter(
            config
        )
    )

    uplift, details = (
        cluster_weighted_uplift(
            condition,
            control,
            direction=direction,
            config=incremental_config,
        )
    )

    if details.empty:
        return None

    condition_metrics = sample_metrics(
        condition,
        direction=direction,
        config=incremental_config,
    )

    control_metrics = sample_metrics(
        control,
        direction=direction,
        config=incremental_config,
    )

    return {
        "condition_observations":
            int(
                condition_metrics[
                    "observation_count"
                ]
            ),
        "control_observations":
            int(
                control_metrics[
                    "observation_count"
                ]
            ),
        "matched_cluster_count":
            int(len(details)),
        "condition_net_mean_return":
            float(
                condition_metrics[
                    "net_mean_return"
                ]
            ),
        "control_net_mean_return":
            float(
                control_metrics[
                    "net_mean_return"
                ]
            ),
        "cluster_matched_uplift":
            float(uplift),
        "condition_net_win_rate":
            float(
                condition_metrics[
                    "net_win_rate"
                ]
            ),
        "control_net_win_rate":
            float(
                control_metrics[
                    "net_win_rate"
                ]
            ),
        "condition_profit_factor":
            float(
                condition_metrics[
                    "profit_factor"
                ]
            ),
        "condition_return_to_mae":
            float(
                condition_metrics[
                    "return_to_mae"
                ]
            ),
    }


def run_discovery_evaluation(
    joined: pd.DataFrame,
    *,
    catalog: pd.DataFrame,
    discovery_folds: tuple[int, ...],
    validation_folds: tuple[int, ...],
    config: MorphologyDiscoveryConfig,
) -> pd.DataFrame:
    rows = []

    discovery_set = set(
        discovery_folds
    )

    validation_set = set(
        validation_folds
    )

    candidates = catalog.to_dict(
        orient="records"
    )

    for fold_id, fold_frame in (
        joined.groupby(
            "fold_id",
            sort=True,
            observed=True,
        )
    ):
        fold_id = int(
            fold_id
        )

        if fold_id in discovery_set:
            phase = "DISCOVERY"
        elif fold_id in validation_set:
            phase = "VALIDATION"
        else:
            continue

        for asset, asset_frame in (
            fold_frame.groupby(
                "asset",
                sort=True,
                observed=True,
            )
        ):
            for direction in (
                "LONG",
                "SHORT",
            ):
                for candidate in candidates:
                    result = (
                        evaluate_candidate_fold(
                            asset_frame,
                            candidate=candidate,
                            direction=direction,
                            config=config,
                        )
                    )

                    if result is None:
                        continue

                    rows.append({
                        "candidate_id":
                            candidate[
                                "candidate_id"
                            ],
                        "candidate_kind":
                            candidate[
                                "candidate_kind"
                            ],
                        "expression":
                            candidate[
                                "expression"
                            ],
                        "fold_id":
                            fold_id,
                        "phase":
                            phase,
                        "asset":
                            str(asset),
                        "direction":
                            direction,
                        **result,
                    })

    columns = [
        "candidate_id",
        "candidate_kind",
        "expression",
        "fold_id",
        "phase",
        "asset",
        "direction",
        "condition_observations",
        "control_observations",
        "matched_cluster_count",
        "condition_net_mean_return",
        "control_net_mean_return",
        "cluster_matched_uplift",
        "condition_net_win_rate",
        "control_net_win_rate",
        "condition_profit_factor",
        "condition_return_to_mae",
    ]

    if not rows:
        return pd.DataFrame(
            columns=columns
        )

    return (
        pd.DataFrame(
            rows,
            columns=columns,
        )
        .sort_values(
            [
                "candidate_id",
                "asset",
                "direction",
                "fold_id",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def exact_sign_test_p_value(
    positive_count: int,
    total_count: int,
) -> float:
    if total_count <= 0:
        return 1.0

    positive_count = int(
        positive_count
    )

    total_count = int(
        total_count
    )

    probability = 0.0

    for successes in range(
        positive_count,
        total_count + 1,
    ):
        probability += (
            math.comb(
                total_count,
                successes,
            )
            * (0.5 ** total_count)
        )

    return float(
        min(
            probability,
            1.0,
        )
    )


def phase_summary(
    group: pd.DataFrame,
    *,
    phase: str,
) -> dict[str, Any]:
    subset = group[
        group[
            "phase"
        ].eq(phase)
    ]

    if subset.empty:
        return {
            f"{phase.lower()}_fold_count":
                0,
            f"{phase.lower()}_observations":
                0,
            f"{phase.lower()}_net_return":
                0.0,
            f"{phase.lower()}_weighted_uplift":
                0.0,
            f"{phase.lower()}_positive_uplift_folds":
                0,
            f"{phase.lower()}_positive_uplift_rate":
                0.0,
            f"{phase.lower()}_sign_test_p_value":
                1.0,
        }

    weights = subset[
        "condition_observations"
    ].clip(lower=1)

    positive_count = int(
        subset[
            "cluster_matched_uplift"
        ].gt(0.0).sum()
    )

    fold_count = int(
        len(subset)
    )

    return {
        f"{phase.lower()}_fold_count":
            fold_count,
        f"{phase.lower()}_observations":
            int(
                subset[
                    "condition_observations"
                ].sum()
            ),
        f"{phase.lower()}_net_return":
            float(
                np.average(
                    subset[
                        "condition_net_mean_return"
                    ],
                    weights=weights,
                )
            ),
        f"{phase.lower()}_weighted_uplift":
            float(
                np.average(
                    subset[
                        "cluster_matched_uplift"
                    ],
                    weights=weights,
                )
            ),
        f"{phase.lower()}_positive_uplift_folds":
            positive_count,
        f"{phase.lower()}_positive_uplift_rate":
            (
                positive_count
                / fold_count
            ),
        f"{phase.lower()}_sign_test_p_value":
            exact_sign_test_p_value(
                positive_count,
                fold_count,
            ),
    }


def summarize_discovery(
    evaluations: pd.DataFrame,
    *,
    config: MorphologyDiscoveryConfig,
) -> pd.DataFrame:
    if evaluations.empty:
        return pd.DataFrame()

    rows = []

    dimensions = (
        "candidate_id",
        "candidate_kind",
        "expression",
        "asset",
        "direction",
    )

    for keys, group in evaluations.groupby(
        list(dimensions),
        sort=True,
        observed=True,
    ):
        (
            candidate_id,
            candidate_kind,
            expression,
            asset,
            direction,
        ) = keys

        discovery = phase_summary(
            group,
            phase="DISCOVERY",
        )

        validation = phase_summary(
            group,
            phase="VALIDATION",
        )

        discovered = bool(
            discovery[
                "discovery_fold_count"
            ]
            >= config.minimum_discovery_folds
            and discovery[
                "discovery_net_return"
            ] > 0.0
            and discovery[
                "discovery_weighted_uplift"
            ]
            > config.minimum_weighted_uplift
            and discovery[
                "discovery_positive_uplift_rate"
            ]
            >= config.minimum_discovery_uplift_rate
        )

        rows.append({
            "candidate_id":
                candidate_id,
            "candidate_kind":
                candidate_kind,
            "expression":
                expression,
            "asset":
                asset,
            "direction":
                direction,
            **discovery,
            **validation,
            "discovered":
                discovered,
        })

    summary = pd.DataFrame(
        rows
    )

    discovered_mask = summary[
        "discovered"
    ].astype(bool)

    summary[
        "validation_bh_adjusted_p_value"
    ] = 1.0

    if discovered_mask.any():
        summary.loc[
            discovered_mask,
            "validation_bh_adjusted_p_value",
        ] = benjamini_hochberg(
            summary.loc[
                discovered_mask,
                "validation_sign_test_p_value",
            ]
        ).to_numpy()

    summary[
        "validated"
    ] = (
        summary[
            "discovered"
        ].astype(bool)
        & summary[
            "validation_fold_count"
        ].ge(
            config.minimum_validation_folds
        )
        & summary[
            "validation_net_return"
        ].gt(0.0)
        & summary[
            "validation_weighted_uplift"
        ].gt(
            config.minimum_weighted_uplift
        )
        & summary[
            "validation_positive_uplift_rate"
        ].ge(
            config.minimum_validation_uplift_rate
        )
        & summary[
            "validation_bh_adjusted_p_value"
        ].le(
            config.multiple_testing_alpha
        )
    )

    return (
        summary.sort_values(
            [
                "validated",
                "discovered",
                "validation_weighted_uplift",
                "discovery_weighted_uplift",
            ],
            ascending=[
                False,
                False,
                False,
                False,
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def write_discovery_outputs(
    *,
    catalog: pd.DataFrame,
    evaluations: pd.DataFrame,
    summary: pd.DataFrame,
    discovery_folds: tuple[int, ...],
    validation_folds: tuple[int, ...],
    config: MorphologyDiscoveryConfig,
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
        "catalog":
            directory
            / "morphology_discovery_catalog.csv",
        "folds":
            directory
            / "morphology_discovery_folds.csv",
        "summary":
            directory
            / "morphology_discovery_summary.csv",
        "validated":
            directory
            / "morphology_discovery_validated.csv",
        "report":
            directory
            / "morphology_discovery_report.json",
    }

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
            "atlas.morphology_discovery.v2",
        "config":
            asdict(config),
        "discovery_folds":
            list(discovery_folds),
        "validation_folds":
            list(validation_folds),
        "catalog_candidates":
            int(len(catalog)),
        "fold_evaluation_rows":
            int(len(evaluations)),
        "summary_rows":
            int(len(summary)),
        "discovered_count":
            int(
                summary[
                    "discovered"
                ].astype(bool).sum()
            ) if not summary.empty else 0,
        "validated_count":
            int(len(validated)),
        "validated_candidates":
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
