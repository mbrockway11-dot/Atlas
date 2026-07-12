"""Atlas Research Experiment Designer v1."""

from __future__ import annotations

from typing import Any

import pandas as pd

from atlas.investment.research_experiment_designer.config import (
    DEFAULT_EMBARGO_DAYS,
    DEFAULT_FOLD_COUNT,
    DEFAULT_MAX_RETENTION_RATIO,
    DEFAULT_MIN_RETENTION_RATIO,
    DEFAULT_MIN_TRADES,
    ELIGIBLE_PROGRAM_STATUS,
    REQUIRED_METRICS,
    SCHEMA_VERSION,
    SOURCE,
)
from atlas.investment.research_experiment_designer.identity import (
    boolean,
    experiment_id,
    number,
    stable_id,
    text,
)


def build_experiment_design_bundle(
    sources: dict[str, Any],
) -> dict[str, pd.DataFrame]:
    programs = sources.get(
        "program_registry",
        pd.DataFrame(),
    )

    members = sources.get(
        "program_members",
        pd.DataFrame(),
    )

    dimensions = sources.get(
        "program_dimensions",
        pd.DataFrame(),
    )

    conflicts = sources.get(
        "program_conflicts",
        pd.DataFrame(),
    )

    candidate_scores = sources.get(
        "candidate_scores",
        pd.DataFrame(),
    )

    state_hash = text(
        sources.get(
            "compiler_report",
            {},
        ).get(
            "state_hash",
            "",
        )
    )

    designs = []
    hypotheses = []
    variants = []
    folds = []
    metrics = []
    criteria = []
    datasets = []
    risks = []
    validations = []

    if programs is None or programs.empty:
        return empty_bundle()

    eligible = programs[
        programs[
            "current_status"
        ].astype(str).eq(
            ELIGIBLE_PROGRAM_STATUS
        )
        & ~programs[
            "is_blocked"
        ].astype(bool)
    ].copy()

    for _, program in eligible.iterrows():
        program_id = text(
            program.get(
                "research_program_id"
            )
        )

        current_experiment_id = (
            experiment_id(
                program_id=program_id,
                state_hash=state_hash,
            )
        )

        program_members = filter_program(
            members,
            program_id,
        )

        program_dimensions = filter_program(
            dimensions,
            program_id,
        )

        program_conflicts = filter_program(
            conflicts,
            program_id,
        )

        enriched_members = enrich_members(
            program_members,
            candidate_scores,
        )

        feature_conditions = build_feature_conditions(
            enriched_members
        )

        hypothesis_text = build_hypothesis(
            program=program,
            feature_conditions=feature_conditions,
        )

        baseline_definition = (
            f"Original unmodified engine: "
            f"{text(program.get('parent_engine_id'))}"
        )

        candidate_definition = (
            "Research-only gated variant retaining "
            "the original signal only when the "
            "program-defined feature conditions permit it."
        )

        designs.append({
            "experiment_id": current_experiment_id,
            "research_program_id": program_id,
            "experiment_version": "1.0.0",
            "experiment_title": (
                f"Experiment: "
                f"{text(program.get('program_title'))}"
            ),
            "parent_engine_id": text(
                program.get(
                    "parent_engine_id"
                )
            ),
            "engine_family": text(
                program.get(
                    "engine_family"
                )
            ),
            "program_priority_score": number(
                program.get(
                    "program_priority_score"
                )
            ),
            "cluster_confidence": number(
                program.get(
                    "cluster_confidence"
                )
            ),
            "hypothesis": hypothesis_text,
            "null_hypothesis": (
                "The proposed gated variant does not "
                "improve out-of-sample risk-adjusted "
                "performance relative to the original engine."
            ),
            "baseline_definition": baseline_definition,
            "candidate_definition": candidate_definition,
            "fold_count": DEFAULT_FOLD_COUNT,
            "embargo_days": DEFAULT_EMBARGO_DAYS,
            "minimum_candidate_trades": DEFAULT_MIN_TRADES,
            "design_status": "DRAFT_COMPLETE",
            "manual_review_required": True,
            "execution_authorized": False,
            "execution_instruction": False,
            "production_eligible": False,
            "state_hash": state_hash,
            "schema_version": SCHEMA_VERSION,
            "source": SOURCE,
        })

        hypotheses.append({
            "hypothesis_id": stable_id(
                "RHYP",
                {
                    "experiment_id": current_experiment_id,
                    "hypothesis": hypothesis_text,
                },
            ),
            "experiment_id": current_experiment_id,
            "research_program_id": program_id,
            "hypothesis_type": "DIRECTIONAL",
            "hypothesis": hypothesis_text,
            "null_hypothesis": (
                "No repeatable out-of-sample improvement."
            ),
            "target_engine_id": text(
                program.get(
                    "parent_engine_id"
                )
            ),
            "execution_instruction": False,
        })

        variants.extend(
            build_variant_rows(
                experiment_id_value=current_experiment_id,
                program_id=program_id,
                members=enriched_members,
            )
        )

        folds.extend(
            build_fold_rows(
                experiment_id_value=current_experiment_id,
            )
        )

        metrics.extend(
            build_metric_rows(
                current_experiment_id
            )
        )

        criteria.extend(
            build_acceptance_rows(
                current_experiment_id
            )
        )

        datasets.extend(
            build_dataset_rows(
                experiment_id_value=current_experiment_id,
                engine_id=text(
                    program.get(
                        "parent_engine_id"
                    )
                ),
            )
        )

        risks.extend(
            build_risk_rows(
                experiment_id_value=current_experiment_id,
                has_conflicts=(
                    not program_conflicts.empty
                    or boolean(
                        program.get(
                            "has_conflicts"
                        )
                    )
                ),
            )
        )

        validation = validate_design(
            experiment_id_value=current_experiment_id,
            program=program,
            member_count=len(
                enriched_members
            ),
            dimension_count=len(
                program_dimensions
            ),
            conflict_count=len(
                program_conflicts
            ),
        )

        validations.extend(
            validation
        )

    return {
        "designs": pd.DataFrame(designs),
        "hypotheses": pd.DataFrame(hypotheses),
        "variants": pd.DataFrame(variants),
        "folds": pd.DataFrame(folds),
        "metrics": pd.DataFrame(metrics),
        "criteria": pd.DataFrame(criteria),
        "datasets": pd.DataFrame(datasets),
        "risks": pd.DataFrame(risks),
        "validation": pd.DataFrame(validations),
    }


def build_hypothesis(
    *,
    program: pd.Series,
    feature_conditions: str,
) -> str:
    engine = text(
        program.get(
            "parent_engine_id"
        )
    )

    if feature_conditions:
        return (
            f"{engine} performance improves when signals "
            f"are gated using the consolidated conditions: "
            f"{feature_conditions}."
        )

    return (
        f"{engine} performance improves when its "
        "consolidated degradation conditions are excluded."
    )


def enrich_members(
    members: pd.DataFrame,
    candidate_scores: pd.DataFrame,
) -> pd.DataFrame:
    if members is None or members.empty:
        return pd.DataFrame()

    if (
        candidate_scores is None
        or candidate_scores.empty
        or "candidate_id"
        not in candidate_scores.columns
    ):
        return members.copy()

    useful_columns = [
        column
        for column in (
            "candidate_id",
            "natural_key",
            "candidate_type",
            "title",
            "parent_engine_id",
            "failure_recurrence_score",
            "validation_potential_score",
            "regime_relevance_score",
            "final_priority_score",
        )
        if column in candidate_scores.columns
    ]

    return members.merge(
        candidate_scores[
            useful_columns
        ],
        on="candidate_id",
        how="left",
        suffixes=(
            "",
            "_score",
        ),
    )


def build_feature_conditions(
    members: pd.DataFrame,
) -> str:
    if members is None or members.empty:
        return ""

    conditions = []

    for _, member in members.iterrows():
        feature = text(
            member.get(
                "feature_name"
            )
        )

        condition = text(
            member.get(
                "condition_value"
            )
        )

        if feature and condition:
            conditions.append(
                f"{feature}={condition}"
            )

    return "; ".join(
        sorted(set(conditions))
    )


def build_variant_rows(
    *,
    experiment_id_value: str,
    program_id: str,
    members: pd.DataFrame,
) -> list[dict]:
    rows = []

    if members is None or members.empty:
        return rows

    for index, member in members.iterrows():
        candidate_id = text(
            member.get(
                "candidate_id"
            )
        )

        feature = text(
            member.get(
                "feature_name"
            )
        )

        condition = text(
            member.get(
                "condition_value"
            )
        )

        gate_expression = (
            f"ALLOW_SIGNAL = NOT "
            f"({feature} == '{condition}')"
            if feature and condition
            else "ALLOW_SIGNAL = PROGRAM_GATE"
        )

        rows.append({
            "experiment_variant_id": stable_id(
                "REXVAR",
                {
                    "experiment_id": experiment_id_value,
                    "candidate_id": candidate_id,
                    "gate_expression": gate_expression,
                },
            ),
            "experiment_id": experiment_id_value,
            "research_program_id": program_id,
            "source_candidate_id": candidate_id,
            "variant_rank": int(
                index
            ) + 1,
            "feature_name": feature,
            "condition_value": condition,
            "gate_expression": gate_expression,
            "candidate_score": number(
                member.get(
                    "candidate_score",
                    member.get(
                        "final_priority_score",
                        0.0,
                    ),
                )
            ),
            "research_only": True,
            "execution_instruction": False,
        })

    return rows


def build_fold_rows(
    *,
    experiment_id_value: str,
) -> list[dict]:
    rows = []

    for fold_number in range(
        1,
        DEFAULT_FOLD_COUNT + 1,
    ):
        rows.append({
            "fold_id": stable_id(
                "RFOLD",
                {
                    "experiment_id": experiment_id_value,
                    "fold_number": fold_number,
                },
            ),
            "experiment_id": experiment_id_value,
            "fold_number": fold_number,
            "training_window": "EXPANDING",
            "test_window": "NON_OVERLAPPING",
            "embargo_days": DEFAULT_EMBARGO_DAYS,
            "uses_future_data": False,
            "overlapping_test_trades": False,
            "execution_instruction": False,
        })

    return rows


def build_metric_rows(
    experiment_id_value: str,
) -> list[dict]:
    return [
        {
            "metric_id": stable_id(
                "RMET",
                {
                    "experiment_id": experiment_id_value,
                    "metric_name": metric_name,
                },
            ),
            "experiment_id": experiment_id_value,
            "metric_name": metric_name,
            "baseline_required": True,
            "candidate_required": True,
            "fold_level_required": True,
            "aggregate_required": True,
            "execution_instruction": False,
        }
        for metric_name in REQUIRED_METRICS
    ]


def build_acceptance_rows(
    experiment_id_value: str,
) -> list[dict]:
    criteria = [
        (
            "minimum_candidate_trades",
            ">=",
            DEFAULT_MIN_TRADES,
        ),
        (
            "fold_win_rate",
            ">=",
            0.66666667,
        ),
        (
            "mean_return_advantage",
            ">",
            0.0,
        ),
        (
            "sharpe_advantage",
            ">",
            0.0,
        ),
        (
            "drawdown_improvement",
            ">=",
            0.0,
        ),
        (
            "retention_ratio",
            ">=",
            DEFAULT_MIN_RETENTION_RATIO,
        ),
        (
            "retention_ratio",
            "<=",
            DEFAULT_MAX_RETENTION_RATIO,
        ),
        (
            "future_data_used",
            "==",
            False,
        ),
        (
            "overlapping_test_trades",
            "==",
            False,
        ),
    ]

    return [
        {
            "criterion_id": stable_id(
                "RCRIT",
                {
                    "experiment_id": experiment_id_value,
                    "criterion": name,
                    "operator": operator,
                    "value": value,
                },
            ),
            "experiment_id": experiment_id_value,
            "criterion_name": name,
            "operator": operator,
            "threshold_value": value,
            "required": True,
            "failure_action": "DO_NOT_PROMOTE",
            "execution_instruction": False,
        }
        for name, operator, value
        in criteria
    ]


def build_dataset_rows(
    *,
    experiment_id_value: str,
    engine_id: str,
) -> list[dict]:
    requirements = [
        (
            "historical_market_data",
            "Historical market observations used by "
            "the original engine.",
        ),
        (
            "historical_engine_signals",
            f"Point-in-time signals from {engine_id}.",
        ),
        (
            "regime_features",
            "Point-in-time regime and feature states.",
        ),
        (
            "trade_outcomes",
            "Non-overlapping realized trade outcomes.",
        ),
    ]

    return [
        {
            "dataset_requirement_id": stable_id(
                "RDATA",
                {
                    "experiment_id": experiment_id_value,
                    "dataset_name": name,
                },
            ),
            "experiment_id": experiment_id_value,
            "dataset_name": name,
            "description": description,
            "point_in_time_required": True,
            "future_data_prohibited": True,
            "required": True,
            "execution_instruction": False,
        }
        for name, description in requirements
    ]


def build_risk_rows(
    *,
    experiment_id_value: str,
    has_conflicts: bool,
) -> list[dict]:
    risks = [
        (
            "LOOKAHEAD_BIAS",
            "HIGH",
            "Use point-in-time features and embargoed folds.",
        ),
        (
            "OVERFITTING",
            "HIGH",
            "Use non-overlapping walk-forward folds and "
            "predeclared acceptance criteria.",
        ),
        (
            "LOW_SAMPLE_SIZE",
            "MEDIUM",
            f"Require at least {DEFAULT_MIN_TRADES} "
            "candidate trades.",
        ),
        (
            "SIGNAL_ATTRITION",
            "MEDIUM",
            "Enforce minimum and maximum retention ratios.",
        ),
    ]

    if has_conflicts:
        risks.append((
            "CONFLICTING_CONDITIONS",
            "HIGH",
            "Resolve condition conflicts before validation.",
        ))

    return [
        {
            "risk_id": stable_id(
                "RRISK",
                {
                    "experiment_id": experiment_id_value,
                    "risk_type": risk_type,
                },
            ),
            "experiment_id": experiment_id_value,
            "risk_type": risk_type,
            "severity": severity,
            "mitigation": mitigation,
            "resolved": False,
            "execution_instruction": False,
        }
        for risk_type, severity, mitigation
        in risks
    ]


def validate_design(
    *,
    experiment_id_value: str,
    program: pd.Series,
    member_count: int,
    dimension_count: int,
    conflict_count: int,
) -> list[dict]:
    checks = [
        (
            "PROGRAM_STATUS_ELIGIBLE",
            text(
                program.get(
                    "current_status"
                )
            ) == ELIGIBLE_PROGRAM_STATUS,
        ),
        (
            "PROGRAM_NOT_BLOCKED",
            not boolean(
                program.get(
                    "is_blocked"
                )
            ),
        ),
        (
            "PARENT_ENGINE_PRESENT",
            bool(
                text(
                    program.get(
                        "parent_engine_id"
                    )
                )
            ),
        ),
        (
            "PROGRAM_MEMBERS_PRESENT",
            member_count > 0,
        ),
        (
            "PROGRAM_DIMENSIONS_PRESENT",
            dimension_count > 0,
        ),
        (
            "NO_UNRESOLVED_CONFLICTS",
            conflict_count == 0,
        ),
    ]

    return [
        {
            "experiment_id": experiment_id_value,
            "check_id": check_id,
            "passed": bool(passed),
            "status": (
                "PASS"
                if passed
                else "FAIL"
            ),
            "execution_instruction": False,
        }
        for check_id, passed in checks
    ]


def filter_program(
    frame: pd.DataFrame,
    program_id: str,
) -> pd.DataFrame:
    if (
        frame is None
        or frame.empty
        or "research_program_id"
        not in frame.columns
    ):
        return pd.DataFrame()

    return frame[
        frame[
            "research_program_id"
        ].astype(str).eq(
            program_id
        )
    ].copy()


def empty_bundle() -> dict[str, pd.DataFrame]:
    return {
        "designs": pd.DataFrame(),
        "hypotheses": pd.DataFrame(),
        "variants": pd.DataFrame(),
        "folds": pd.DataFrame(),
        "metrics": pd.DataFrame(),
        "criteria": pd.DataFrame(),
        "datasets": pd.DataFrame(),
        "risks": pd.DataFrame(),
        "validation": pd.DataFrame(),
    }
