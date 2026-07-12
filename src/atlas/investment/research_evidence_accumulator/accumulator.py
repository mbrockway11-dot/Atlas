"""Atlas Research Evidence Accumulator v1 engine."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd

from atlas.investment.research_evidence_accumulator.analysis import (
    calculate_consistency,
    calculate_contradictions,
    calculate_decay,
    calculate_sufficiency,
)
from atlas.investment.research_evidence_accumulator.config import (
    ELIGIBLE_PROGRAM_STATUSES,
    EVIDENCE_WEIGHTS,
    MAXIMUM_CONTRADICTION_RATE,
    MAXIMUM_DECAY_RATE,
    MINIMUM_CONSISTENCY_SCORE,
    MINIMUM_FOLD_WIN_RATE,
    MINIMUM_RUN_PASS_RATE,
)
from atlas.investment.research_evidence_accumulator.identity import (
    boolean,
    clamp,
    number,
    safe_mean,
    stable_id,
    text,
)


def build_accumulated_evidence(
    *,
    program_registry: pd.DataFrame,
    run_history: pd.DataFrame,
    variant_history: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    consistency = calculate_consistency(
        variant_history
    )

    contradictions = (
        calculate_contradictions(
            variant_history
        )
    )

    decay = calculate_decay(
        variant_history,
        run_history,
    )

    sufficiency = calculate_sufficiency(
        variant_history,
        run_history,
    )

    variant_evidence = combine_variant_evidence(
        variant_history=variant_history,
        consistency=consistency,
        contradictions=contradictions,
        decay=decay,
        sufficiency=sufficiency,
    )

    experiment_evidence = (
        aggregate_experiment_evidence(
            variant_evidence
        )
    )

    recommendations = (
        build_program_recommendations(
            program_registry=program_registry,
            experiment_evidence=experiment_evidence,
        )
    )

    run_lineage = build_run_lineage(
        run_history,
        variant_history,
    )

    return {
        "experiment_evidence": (
            experiment_evidence
        ),
        "variant_evidence": (
            variant_evidence
        ),
        "run_lineage": run_lineage,
        "consistency": consistency,
        "decay": decay,
        "contradictions": contradictions,
        "sufficiency": sufficiency,
        "recommendations": recommendations,
    }


def combine_variant_evidence(
    *,
    variant_history: pd.DataFrame,
    consistency: pd.DataFrame,
    contradictions: pd.DataFrame,
    decay: pd.DataFrame,
    sufficiency: pd.DataFrame,
) -> pd.DataFrame:
    if (
        variant_history is None
        or variant_history.empty
    ):
        return pd.DataFrame()

    grouped = (
        variant_history.groupby(
            [
                "research_program_id",
                "experiment_id",
                "experiment_variant_id",
            ],
            dropna=False,
        )
        .agg(
            source_candidate_id=(
                "source_candidate_id",
                "first",
            ),
            gate_expression=(
                "gate_expression",
                "first",
            ),
            run_count=(
                "run_id",
                "nunique",
            ),
            baseline_trade_count=(
                "baseline_trade_count",
                lambda series: int(
                    series.map(number).sum()
                ),
            ),
            candidate_trade_count=(
                "candidate_trade_count",
                lambda series: int(
                    series.map(number).sum()
                ),
            ),
            mean_retention_ratio=(
                "retention_ratio",
                lambda series: safe_mean(
                    series.map(number).tolist()
                ),
            ),
            mean_return_advantage=(
                "mean_return_advantage",
                lambda series: safe_mean(
                    series.map(number).tolist()
                ),
            ),
            mean_sharpe_advantage=(
                "sharpe_advantage",
                lambda series: safe_mean(
                    series.map(number).tolist()
                ),
            ),
            mean_drawdown_improvement=(
                "drawdown_improvement",
                lambda series: safe_mean(
                    series.map(number).tolist()
                ),
            ),
            mean_fold_win_rate=(
                "fold_win_rate",
                lambda series: safe_mean(
                    series.map(number).tolist()
                ),
            ),
            passing_run_count=(
                "acceptance_passed",
                lambda series: int(
                    series.map(boolean).sum()
                ),
            ),
        )
        .reset_index()
    )

    merge_keys = [
        "research_program_id",
        "experiment_variant_id",
    ]

    for frame in (
        consistency,
        contradictions,
        decay,
        sufficiency,
    ):
        if frame is None or frame.empty:
            continue

        frame = frame.copy()

        keep = [
            column
            for column in frame.columns
            if (
                column in merge_keys
                or column not in grouped.columns
            )
        ]

        grouped = grouped.merge(
            frame[keep],
            on=merge_keys,
            how="left",
        )

    grouped[
        "run_pass_rate"
    ] = (
        grouped[
            "passing_run_count"
        ]
        / grouped[
            "run_count"
        ].clip(lower=1)
    )

    grouped[
        "sample_sufficiency_score"
    ] = grouped.get(
        "sufficiency_score",
        0.0,
    ).fillna(0.0)

    grouped[
        "state_diversity_score"
    ] = (
        grouped.get(
            "distinct_state_hashes",
            0,
        )
        .fillna(0)
        .map(
            lambda value: clamp(
                number(value) / 3.0
            )
        )
    )

    grouped[
        "recency_score"
    ] = 1.0

    grouped[
        "evidence_score"
    ] = grouped.apply(
        calculate_variant_evidence_score,
        axis=1,
    )

    grouped[
        "durability_status"
    ] = grouped.apply(
        classify_durability,
        axis=1,
    )

    grouped[
        "execution_instruction"
    ] = False

    grouped[
        "program_transition_authorized"
    ] = False

    grouped[
        "implementation_authorized"
    ] = False

    grouped[
        "production_eligible"
    ] = False

    return grouped.sort_values(
        [
            "research_program_id",
            "evidence_score",
            "experiment_variant_id",
        ],
        ascending=[
            True,
            False,
            True,
        ],
        kind="stable",
    ).reset_index(drop=True)


def calculate_variant_evidence_score(
    row: pd.Series,
) -> float:
    contradiction_penalty = clamp(
        number(
            row.get(
                "contradiction_rate"
            )
        )
    )

    decay_penalty = clamp(
        number(
            row.get(
                "decay_rate"
            )
        )
    )

    positive_mean_score = (
        1.0
        if number(
            row.get(
                "mean_return_advantage"
            )
        ) > 0
        else 0.0
    )

    positive_sharpe_score = (
        1.0
        if number(
            row.get(
                "mean_sharpe_advantage"
            )
        ) > 0
        else 0.0
    )

    drawdown_score = (
        1.0
        if number(
            row.get(
                "mean_drawdown_improvement"
            )
        ) >= 0
        else 0.0
    )

    score = (
        clamp(
            number(
                row.get(
                    "run_pass_rate"
                )
            )
        )
        * EVIDENCE_WEIGHTS[
            "run_pass_rate"
        ]
        + clamp(
            number(
                row.get(
                    "fold_consistency_rate"
                )
            )
        )
        * EVIDENCE_WEIGHTS[
            "fold_consistency"
        ]
        + positive_mean_score
        * EVIDENCE_WEIGHTS[
            "mean_return_consistency"
        ]
        + positive_sharpe_score
        * EVIDENCE_WEIGHTS[
            "sharpe_consistency"
        ]
        + drawdown_score
        * EVIDENCE_WEIGHTS[
            "drawdown_consistency"
        ]
        + clamp(
            number(
                row.get(
                    "sample_sufficiency_score"
                )
            )
        )
        * EVIDENCE_WEIGHTS[
            "sample_sufficiency"
        ]
        + clamp(
            number(
                row.get(
                    "state_diversity_score"
                )
            )
        )
        * EVIDENCE_WEIGHTS[
            "state_diversity"
        ]
        + clamp(
            number(
                row.get(
                    "recency_score"
                )
            )
        )
        * EVIDENCE_WEIGHTS[
            "recency"
        ]
        - contradiction_penalty
        * 0.15
        - decay_penalty
        * 0.15
    )

    return clamp(score)


def classify_durability(
    row: pd.Series,
) -> str:
    if (
        number(
            row.get(
                "contradiction_rate"
            )
        )
        > MAXIMUM_CONTRADICTION_RATE
    ):
        return "CONTRADICTORY"

    if (
        number(
            row.get(
                "decay_rate"
            )
        )
        > MAXIMUM_DECAY_RATE
    ):
        return "DECAYING"

    if not boolean(
        row.get(
            "evidence_sufficient"
        )
    ):
        return "INSUFFICIENT"

    if (
        number(
            row.get(
                "consistency_score"
            )
        )
        >= MINIMUM_CONSISTENCY_SCORE
        and number(
            row.get(
                "run_pass_rate"
            )
        )
        >= MINIMUM_RUN_PASS_RATE
    ):
        return "DURABLE"

    return "MIXED"


def aggregate_experiment_evidence(
    variant_evidence: pd.DataFrame,
) -> pd.DataFrame:
    if (
        variant_evidence is None
        or variant_evidence.empty
    ):
        return pd.DataFrame()

    rows = []

    grouped = variant_evidence.groupby(
        [
            "research_program_id",
            "experiment_id",
        ],
        dropna=False,
    )

    for (
        program_id,
        experiment_id,
    ), group in grouped:
        ordered = group.sort_values(
            "evidence_score",
            ascending=False,
            kind="stable",
        )

        best = ordered.iloc[0]

        rows.append({
            "evidence_accumulation_id": (
                stable_id(
                    "REVID",
                    {
                        "program_id": program_id,
                        "experiment_id": experiment_id,
                        "variant_ids": sorted(
                            group[
                                "experiment_variant_id"
                            ].astype(str).tolist()
                        ),
                    },
                )
            ),
            "research_program_id": text(
                program_id
            ),
            "experiment_id": text(
                experiment_id
            ),
            "variant_count": int(
                len(group)
            ),
            "durable_variant_count": int(
                group[
                    "durability_status"
                ].astype(str).eq(
                    "DURABLE"
                ).sum()
            ),
            "contradictory_variant_count": int(
                group[
                    "durability_status"
                ].astype(str).eq(
                    "CONTRADICTORY"
                ).sum()
            ),
            "decaying_variant_count": int(
                group[
                    "durability_status"
                ].astype(str).eq(
                    "DECAYING"
                ).sum()
            ),
            "best_variant_id": text(
                best.get(
                    "experiment_variant_id"
                )
            ),
            "best_variant_evidence_score": (
                number(
                    best.get(
                        "evidence_score"
                    )
                )
            ),
            "best_variant_durability": text(
                best.get(
                    "durability_status"
                )
            ),
            "mean_variant_evidence_score": (
                safe_mean(
                    group[
                        "evidence_score"
                    ].map(number).tolist()
                )
            ),
            "total_run_count": int(
                group[
                    "run_count"
                ].map(number).sum()
            ),
            "total_candidate_trades": int(
                group[
                    "candidate_trade_count"
                ].map(number).sum()
            ),
            "execution_instruction": False,
            "program_transition_authorized": False,
        })

    return pd.DataFrame(rows)


def build_program_recommendations(
    *,
    program_registry: pd.DataFrame,
    experiment_evidence: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    if (
        experiment_evidence is None
        or experiment_evidence.empty
    ):
        return pd.DataFrame()

    for _, evidence in (
        experiment_evidence.iterrows()
    ):
        program_id = text(
            evidence.get(
                "research_program_id"
            )
        )

        program = filter_program(
            program_registry,
            program_id,
        )

        current_status = (
            text(
                program.iloc[0].get(
                    "current_status"
                )
            )
            if not program.empty
            else ""
        )

        eligible_status = (
            current_status
            in ELIGIBLE_PROGRAM_STATUSES
        )

        durability = text(
            evidence.get(
                "best_variant_durability"
            )
        )

        evidence_score = number(
            evidence.get(
                "best_variant_evidence_score"
            )
        )

        if not eligible_status:
            recommendation = (
                "NO_LIFECYCLE_RECOMMENDATION"
            )
            reason = (
                "Program is not currently in an "
                "evidence-eligible lifecycle state."
            )
        elif durability == "DURABLE":
            recommendation = (
                "RECOMMEND_EVIDENCE_ACCUMULATING"
            )
            reason = (
                "At least one variant has sufficient, "
                "consistent, non-decaying evidence."
            )
        elif durability == "DECAYING":
            recommendation = (
                "RECOMMEND_REVALIDATION"
            )
            reason = (
                "Recent evidence is materially weaker "
                "than earlier evidence."
            )
        elif durability == "CONTRADICTORY":
            recommendation = (
                "RECOMMEND_DEFER"
            )
            reason = (
                "Evidence changes direction across runs "
                "or state hashes."
            )
        elif durability == "INSUFFICIENT":
            recommendation = (
                "CONTINUE_VALIDATING"
            )
            reason = (
                "More completed runs, state diversity, "
                "folds, or candidate trades are required."
            )
        else:
            recommendation = (
                "CONTINUE_VALIDATING"
            )
            reason = (
                "Evidence is mixed and does not yet "
                "support lifecycle advancement."
            )

        rows.append({
            "research_program_id": (
                program_id
            ),
            "current_status": (
                current_status
            ),
            "experiment_id": text(
                evidence.get(
                    "experiment_id"
                )
            ),
            "best_variant_id": text(
                evidence.get(
                    "best_variant_id"
                )
            ),
            "best_variant_evidence_score": (
                evidence_score
            ),
            "best_variant_durability": (
                durability
            ),
            "recommendation": (
                recommendation
            ),
            "recommendation_reason": (
                reason
            ),
            "manual_review_required": True,
            "program_transition_authorized": False,
            "execution_instruction": False,
            "implementation_authorized": False,
            "production_eligible": False,
        })

    return pd.DataFrame(rows)


def build_run_lineage(
    run_history: pd.DataFrame,
    variant_history: pd.DataFrame,
) -> pd.DataFrame:
    if (
        run_history is None
        or run_history.empty
    ):
        return pd.DataFrame()

    variant_counts = (
        variant_history.groupby(
            "run_id"
        )
        .agg(
            evaluated_variant_count=(
                "experiment_variant_id",
                "nunique",
            ),
            passing_variant_count=(
                "acceptance_passed",
                lambda series: int(
                    series.map(boolean).sum()
                ),
            ),
        )
        .reset_index()
        if (
            variant_history is not None
            and not variant_history.empty
        )
        else pd.DataFrame()
    )

    result = run_history.copy()

    if not variant_counts.empty:
        result = result.merge(
            variant_counts,
            on="run_id",
            how="left",
        )

    result[
        "execution_instruction"
    ] = False

    return result


def filter_program(
    registry: pd.DataFrame,
    program_id: str,
) -> pd.DataFrame:
    if (
        registry is None
        or registry.empty
        or "research_program_id"
        not in registry.columns
    ):
        return pd.DataFrame()

    return registry[
        registry[
            "research_program_id"
        ].astype(str).eq(
            program_id
        )
    ].copy()

