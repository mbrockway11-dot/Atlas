"""Variant Review Board v1 scoring."""

from __future__ import annotations

import math

import pandas as pd


BOARD_COLUMNS = [
    "review_rank",
    "variant_id",
    "variant_name",
    "hypothesis_id",
    "hypothesis_type",
    "parent_engine_id",
    "parent_engine_family",
    "gate_mode",
    "feature",
    "target_state",
    "gate_expression",
    "validation_score",
    "fold_win_rate",
    "valid_fold_count",
    "candidate_trade_count",
    "retention_ratio",
    "mean_return_advantage",
    "sharpe_advantage",
    "drawdown_improvement",
    "evidence_score",
    "stability_score",
    "risk_improvement_score",
    "learning_score",
    "governance_score",
    "meta_priority_score",
    "complexity_score",
    "overall_review_score",
    "recommended_decision",
    "decision_reason",
    "review_status",
    "manual_decision",
    "manual_reviewer",
    "manual_rationale",
    "implementation_priority",
    "has_registry_conflict",
    "production_eligible",
    "execution_instruction",
]


def build_review_board(
    registry: pd.DataFrame,
    maps: dict,
) -> pd.DataFrame:
    """Score all immutable validated variants."""
    if registry is None or registry.empty:
        return pd.DataFrame(
            columns=BOARD_COLUMNS
        )

    rows = []

    for _, variant in registry.iterrows():
        variant_id = text(
            variant.get(
                "variant_id"
            )
        )

        hypothesis_id = text(
            variant.get(
                "hypothesis_id"
            )
        )

        engine_id = text(
            variant.get(
                "parent_engine_id"
            )
        )

        fold = maps[
            "folds"
        ].get(
            hypothesis_id,
            {},
        )

        priority = maps[
            "priorities"
        ].get(
            hypothesis_id,
            {},
        )

        learning = maps[
            "learning"
        ].get(
            engine_id,
            {},
        )

        governance = maps[
            "governance"
        ].get(
            engine_id,
            {},
        )

        performance = maps[
            "performance"
        ].get(
            engine_id,
            {},
        )

        conflict = (
            variant_id
            in maps["conflicts"]
        )

        validation_score = number(
            variant.get(
                "validation_score"
            )
        )

        fold_win_rate = number(
            variant.get(
                "fold_win_rate",
                fold.get(
                    "fold_win_rate"
                ),
            )
        )

        valid_fold_count = integer(
            variant.get(
                "valid_fold_count",
                fold.get(
                    "fold_count"
                ),
            )
        )

        candidate_trade_count = integer(
            variant.get(
                "candidate_trade_count",
                fold.get(
                    "total_candidate_trades"
                ),
            )
        )

        retention_ratio = number(
            variant.get(
                "retention_ratio"
            )
        )

        mean_advantage = number(
            variant.get(
                "mean_return_advantage"
            )
        )

        sharpe_advantage = number(
            variant.get(
                "sharpe_advantage"
            )
        )

        drawdown_improvement = number(
            variant.get(
                "drawdown_improvement"
            )
        )

        evidence_score = score_evidence(
            validation_score=(
                validation_score
            ),
            valid_fold_count=(
                valid_fold_count
            ),
            candidate_trade_count=(
                candidate_trade_count
            ),
            retention_ratio=(
                retention_ratio
            ),
        )

        stability_score = score_stability(
            fold_win_rate=fold_win_rate,
            fold_count=valid_fold_count,
            fold_std=number(
                fold.get(
                    "fold_mean_advantage_std"
                )
            ),
        )

        risk_score = score_risk(
            mean_advantage=mean_advantage,
            sharpe_advantage=(
                sharpe_advantage
            ),
            drawdown_improvement=(
                drawdown_improvement
            ),
        )

        learning_score = clamp(
            number(
                learning.get(
                    "learning_reliability",
                    0.50,
                ),
                default=0.50,
            )
            * 0.70
            + number(
                learning.get(
                    "decision_stability",
                    0.50,
                ),
                default=0.50,
            )
            * 0.30
        )

        governance_score = score_governance(
            governance
        )

        meta_priority = clamp(
            number(
                priority.get(
                    "meta_priority_score",
                    0.50,
                ),
                default=0.50,
            )
        )

        complexity_score = score_complexity(
            variant
        )

        overall = calculate_overall_score(
            evidence=evidence_score,
            stability=stability_score,
            risk=risk_score,
            learning=learning_score,
            governance=governance_score,
            meta_priority=meta_priority,
            complexity=complexity_score,
            conflict=conflict,
        )

        decision, reason = recommend_decision(
            overall_score=overall,
            validation_score=validation_score,
            fold_win_rate=fold_win_rate,
            valid_fold_count=valid_fold_count,
            candidate_trade_count=(
                candidate_trade_count
            ),
            retention_ratio=retention_ratio,
            mean_advantage=mean_advantage,
            sharpe_advantage=(
                sharpe_advantage
            ),
            drawdown_improvement=(
                drawdown_improvement
            ),
            conflict=conflict,
        )

        rows.append({
            "variant_id": variant_id,
            "variant_name": text(
                variant.get(
                    "variant_name"
                )
            ),
            "hypothesis_id": hypothesis_id,
            "hypothesis_type": text(
                variant.get(
                    "hypothesis_type"
                )
            ),
            "parent_engine_id": engine_id,
            "parent_engine_family": text(
                variant.get(
                    "parent_engine_family"
                )
            ),
            "gate_mode": text(
                variant.get(
                    "gate_mode"
                )
            ),
            "feature": text(
                variant.get(
                    "feature"
                )
            ),
            "target_state": text(
                variant.get(
                    "target_state"
                )
            ),
            "gate_expression": text(
                variant.get(
                    "gate_expression"
                )
            ),
            "validation_score": round(
                validation_score,
                8,
            ),
            "fold_win_rate": round(
                fold_win_rate,
                8,
            ),
            "valid_fold_count": (
                valid_fold_count
            ),
            "candidate_trade_count": (
                candidate_trade_count
            ),
            "retention_ratio": round(
                retention_ratio,
                8,
            ),
            "mean_return_advantage": round(
                mean_advantage,
                8,
            ),
            "sharpe_advantage": round(
                sharpe_advantage,
                8,
            ),
            "drawdown_improvement": round(
                drawdown_improvement,
                8,
            ),
            "evidence_score": round(
                evidence_score,
                8,
            ),
            "stability_score": round(
                stability_score,
                8,
            ),
            "risk_improvement_score": round(
                risk_score,
                8,
            ),
            "learning_score": round(
                learning_score,
                8,
            ),
            "governance_score": round(
                governance_score,
                8,
            ),
            "meta_priority_score": round(
                meta_priority,
                8,
            ),
            "complexity_score": round(
                complexity_score,
                8,
            ),
            "overall_review_score": round(
                overall * 100.0,
                4,
            ),
            "recommended_decision": (
                decision
            ),
            "decision_reason": reason,
            "review_status": (
                "PENDING_MANUAL_REVIEW"
            ),
            "manual_decision": "",
            "manual_reviewer": "",
            "manual_rationale": "",
            "implementation_priority": "",
            "has_registry_conflict": (
                conflict
            ),
            "production_eligible": False,
            "execution_instruction": False,
        })

    board = pd.DataFrame(rows)

    board = board.sort_values(
        [
            "overall_review_score",
            "validation_score",
            "fold_win_rate",
            "variant_id",
        ],
        ascending=[
            False,
            False,
            False,
            True,
        ],
        kind="stable",
    ).reset_index(drop=True)

    board.insert(
        0,
        "review_rank",
        range(
            1,
            len(board) + 1,
        ),
    )

    board[
        "implementation_priority"
    ] = board.apply(
        assign_priority,
        axis=1,
    )

    return board[
        BOARD_COLUMNS
    ]


def score_evidence(
    *,
    validation_score: float,
    valid_fold_count: int,
    candidate_trade_count: int,
    retention_ratio: float,
) -> float:
    fold_score = min(
        1.0,
        valid_fold_count / 8.0,
    )

    sample_score = min(
        1.0,
        candidate_trade_count / 150.0,
    )

    retention_score = min(
        1.0,
        retention_ratio / 0.75,
    )

    return clamp(
        validation_score * 0.40
        + fold_score * 0.20
        + sample_score * 0.25
        + retention_score * 0.15
    )


def score_stability(
    *,
    fold_win_rate: float,
    fold_count: int,
    fold_std: float,
) -> float:
    count_score = min(
        1.0,
        fold_count / 8.0,
    )

    dispersion_penalty = min(
        1.0,
        fold_std / 0.05,
    )

    return clamp(
        fold_win_rate * 0.65
        + count_score * 0.25
        + (
            1.0
            - dispersion_penalty
        ) * 0.10
    )


def score_risk(
    *,
    mean_advantage: float,
    sharpe_advantage: float,
    drawdown_improvement: float,
) -> float:
    mean_score = clamp(
        mean_advantage / 0.04
    )

    sharpe_score = clamp(
        sharpe_advantage / 0.60
    )

    drawdown_score = clamp(
        drawdown_improvement / 0.30
    )

    return clamp(
        mean_score * 0.35
        + sharpe_score * 0.30
        + drawdown_score * 0.35
    )


def score_governance(
    governance: dict,
) -> float:
    if not governance:
        return 0.50

    eligible_score = (
        1.0
        if governance.get(
            "governance_eligible",
            False,
        )
        else 0.35
    )

    suitability = clamp(
        number(
            governance.get(
                "regime_suitability",
                0.50,
            ),
            default=0.50,
        )
    )

    fusion = clamp(
        number(
            governance.get(
                "fusion_modifier",
                1.0,
            ),
            default=1.0,
        ) / 1.20
    )

    return clamp(
        eligible_score * 0.45
        + suitability * 0.35
        + fusion * 0.20
    )


def score_complexity(
    variant: pd.Series,
) -> float:
    gate_mode = text(
        variant.get(
            "gate_mode"
        )
    )

    feature = text(
        variant.get(
            "feature"
        )
    )

    complexity = 0.20

    if gate_mode == "INCLUDE_ONLY_WHEN":
        complexity += 0.10

    if (
        "state" not in feature.lower()
        and "regime" not in feature.lower()
    ):
        complexity += 0.10

    return clamp(complexity)


def calculate_overall_score(
    *,
    evidence: float,
    stability: float,
    risk: float,
    learning: float,
    governance: float,
    meta_priority: float,
    complexity: float,
    conflict: bool,
) -> float:
    score = (
        evidence * 0.26
        + stability * 0.20
        + risk * 0.22
        + learning * 0.10
        + governance * 0.08
        + meta_priority * 0.09
        + (
            1.0 - complexity
        ) * 0.05
    )

    if conflict:
        score *= 0.40

    return clamp(score)


def recommend_decision(
    *,
    overall_score: float,
    validation_score: float,
    fold_win_rate: float,
    valid_fold_count: int,
    candidate_trade_count: int,
    retention_ratio: float,
    mean_advantage: float,
    sharpe_advantage: float,
    drawdown_improvement: float,
    conflict: bool,
) -> tuple[str, str]:
    if conflict:
        return (
            "REJECT",
            "Immutable registry conflict detected.",
        )

    approve_conditions = [
        validation_score >= 0.85,
        fold_win_rate >= 0.65,
        valid_fold_count >= 4,
        candidate_trade_count >= 50,
        retention_ratio >= 0.30,
        mean_advantage >= 0.005,
        sharpe_advantage >= 0.15,
        drawdown_improvement >= 0.05,
    ]

    if all(approve_conditions):
        return (
            "APPROVE",
            "Variant passed all evidence, stability, sample, "
            "return, Sharpe, and drawdown review gates.",
        )

    if (
        overall_score >= 0.60
        and mean_advantage > 0
        and sharpe_advantage > 0
    ):
        return (
            "HOLD",
            "Variant is promising but misses at least one "
            "approval threshold.",
        )

    if (
        overall_score >= 0.45
        or valid_fold_count < 4
        or candidate_trade_count < 50
    ):
        return (
            "REQUEST_MORE_RESEARCH",
            "Variant requires more folds, observations, "
            "or refined gating analysis.",
        )

    return (
        "REJECT",
        "Variant lacks sufficient evidence or risk-adjusted value.",
    )


def assign_priority(
    row: pd.Series,
) -> str:
    if (
        row[
            "recommended_decision"
        ]
        != "APPROVE"
    ):
        return ""

    score = float(
        row[
            "overall_review_score"
        ]
    )

    if score >= 85:
        return "P1"

    if score >= 75:
        return "P2"

    return "P3"


def clamp(
    value: float,
) -> float:
    return max(
        0.0,
        min(
            1.0,
            number(value),
        ),
    )


def number(
    value,
    *,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default

    return (
        result
        if math.isfinite(result)
        else default
    )


def integer(
    value,
    *,
    default: int = 0,
) -> int:
    try:
        return int(
            float(value)
        )
    except (
        TypeError,
        ValueError,
    ):
        return default


def text(
    value,
) -> str:
    if value is None:
        return ""

    return str(value)
