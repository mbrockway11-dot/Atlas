"""Bridge accumulated research evidence into validated variants."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pandas as pd

from atlas.investment.validated_variants.builder import (
    REGISTRY_COLUMNS,
    build_variant_id,
    build_variant_name,
    hash_specification,
)
from atlas.investment.validated_variants.config import (
    IMPLEMENTATION_STATUS,
    PRODUCTION_STATUS,
    RESEARCH_STATUS,
    REVIEW_STATUS,
    SCHEMA_VERSION,
    VERSION,
)


QUALIFYING_RECOMMENDATION = (
    "RECOMMEND_EVIDENCE_ACCUMULATING"
)

QUALIFYING_DURABILITY = "DURABLE"


def build_accumulated_evidence_variants(
    *,
    accumulated_evidence: pd.DataFrame,
    program_recommendations: pd.DataFrame,
    experiment_variants: pd.DataFrame,
    experiment_designs: pd.DataFrame,
) -> pd.DataFrame:
    """Convert only durable accumulated evidence into registry rows."""
    if (
        accumulated_evidence is None
        or accumulated_evidence.empty
        or program_recommendations is None
        or program_recommendations.empty
        or experiment_variants is None
        or experiment_variants.empty
        or experiment_designs is None
        or experiment_designs.empty
    ):
        return pd.DataFrame(
            columns=REGISTRY_COLUMNS
        )

    evidence = accumulated_evidence.copy()
    recommendations = (
        program_recommendations.copy()
    )
    variants = experiment_variants.copy()
    designs = experiment_designs.copy()

    evidence = evidence[
        evidence[
            "durability_status"
        ].astype(str).eq(
            QUALIFYING_DURABILITY
        )
        & evidence[
            "evidence_sufficient"
        ].map(boolean)
    ].copy()

    recommendations = recommendations[
        recommendations[
            "recommendation"
        ].astype(str).eq(
            QUALIFYING_RECOMMENDATION
        )
    ].copy()

    if evidence.empty or recommendations.empty:
        return pd.DataFrame(
            columns=REGISTRY_COLUMNS
        )

    evidence = evidence.merge(
        recommendations[
            [
                "research_program_id",
                "experiment_id",
                "recommendation",
                "recommendation_reason",
            ]
        ],
        on=[
            "research_program_id",
            "experiment_id",
        ],
        how="inner",
    )

    evidence = evidence.merge(
        variants[
            [
                "experiment_variant_id",
                "experiment_id",
                "source_candidate_id",
                "feature_name",
                "condition_value",
                "gate_expression",
            ]
        ],
        on=[
            "experiment_variant_id",
            "experiment_id",
        ],
        how="inner",
        suffixes=(
            "",
            "_design",
        ),
    )

    evidence = evidence.merge(
        designs[
            [
                "experiment_id",
                "research_program_id",
                "parent_engine_id",
                "engine_family",
                "hypothesis",
                "null_hypothesis",
            ]
        ],
        on=[
            "experiment_id",
            "research_program_id",
        ],
        how="inner",
    )

    observed_at = datetime.now(
        UTC
    ).isoformat()

    rows = []

    for _, row in evidence.iterrows():
        engine_id = text(
            row.get(
                "parent_engine_id"
            )
        )

        family = text(
            row.get(
                "engine_family"
            )
        )

        feature = text(
            row.get(
                "feature_name"
            )
        )

        target_state = text(
            row.get(
                "condition_value"
            )
        ).upper()

        experiment_variant_id = text(
            row.get(
                "experiment_variant_id"
            )
        )

        program_id = text(
            row.get(
                "research_program_id"
            )
        )

        hypothesis_id = (
            f"REVIDHYP-{experiment_variant_id}"
        )

        hypothesis_type = (
            "FAILURE_MODE_GATE"
        )

        gate_mode = "EXCLUDE_WHEN"

        gate_expression = text(
            row.get(
                "gate_expression"
            )
        )

        variant_id = build_variant_id(
            parent_engine_id=engine_id,
            hypothesis_type=hypothesis_type,
            feature=feature,
            state=target_state,
        )

        conditions_passed = json.dumps(
            {
                "durability_status": text(
                    row.get(
                        "durability_status"
                    )
                ),
                "evidence_sufficient": boolean(
                    row.get(
                        "evidence_sufficient"
                    )
                ),
                "run_pass_rate": number(
                    row.get(
                        "run_pass_rate"
                    )
                ),
                "consistency_score": number(
                    row.get(
                        "consistency_score"
                    )
                ),
                "contradiction_rate": number(
                    row.get(
                        "contradiction_rate"
                    )
                ),
                "decay_rate": number(
                    row.get(
                        "decay_rate"
                    )
                ),
                "research_program_id": program_id,
                "experiment_id": text(
                    row.get(
                        "experiment_id"
                    )
                ),
                "experiment_variant_id": (
                    experiment_variant_id
                ),
            },
            sort_keys=True,
        )

        specification_core = {
            "variant_id": variant_id,
            "schema_version": SCHEMA_VERSION,
            "registry_version": VERSION,
            "hypothesis_id": hypothesis_id,
            "hypothesis_type": (
                hypothesis_type
            ),
            "parent_engine_id": engine_id,
            "parent_engine_family": family,
            "variant_name": build_variant_name(
                engine_id=engine_id,
                gate_mode=gate_mode,
                feature=feature,
                state=target_state,
            ),
            "gate_mode": gate_mode,
            "feature": feature,
            "target_state": target_state,
            "gate_expression": (
                gate_expression
            ),
            "research_status": (
                RESEARCH_STATUS
            ),
            "review_status": REVIEW_STATUS,
            "implementation_status": (
                IMPLEMENTATION_STATUS
            ),
            "production_status": (
                PRODUCTION_STATUS
            ),
            "validation_score": number(
                row.get(
                    "evidence_score"
                )
            ),
            "valid_fold_count": integer(
                row.get(
                    "total_fold_count"
                )
            ),
            "baseline_trade_count": integer(
                row.get(
                    "baseline_trade_count"
                )
            ),
            "candidate_trade_count": integer(
                row.get(
                    "candidate_trade_count"
                )
            ),
            "retention_ratio": number(
                row.get(
                    "mean_retention_ratio"
                )
            ),
            "fold_win_rate": number(
                row.get(
                    "mean_fold_win_rate"
                )
            ),
            "mean_return_advantage": number(
                row.get(
                    "mean_return_advantage"
                )
            ),
            "profit_factor_advantage": 0.0,
            "sharpe_advantage": number(
                row.get(
                    "mean_sharpe_advantage"
                )
            ),
            "drawdown_improvement": number(
                row.get(
                    "mean_drawdown_improvement"
                )
            ),
            "conditions_passed": (
                conditions_passed
            ),
            "hard_failures": "",
            "thesis": text(
                row.get(
                    "hypothesis"
                )
            ),
            "proposed_test": (
                "Review accumulated longitudinal "
                "evidence through the existing "
                "Variant Review Board."
            ),
            "validation_requirement": (
                "Manual review remains required. "
                "No implementation or production "
                "authorization is implied."
            ),
            "immutable": True,
            "manual_approval_required": True,
            "execution_instruction": False,
            "source": (
                "research_evidence_accumulator_v1"
            ),
        }

        rows.append({
            **specification_core,
            "specification_hash": (
                hash_specification(
                    specification_core
                )
            ),
            "created_at": observed_at,
            "last_observed_at": observed_at,
        })

    if not rows:
        return pd.DataFrame(
            columns=REGISTRY_COLUMNS
        )

    return pd.DataFrame(
        rows,
        columns=REGISTRY_COLUMNS,
    ).sort_values(
        [
            "parent_engine_id",
            "feature",
            "target_state",
            "variant_id",
        ],
        kind="stable",
    ).reset_index(drop=True)


def number(
    value,
    *,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def integer(
    value,
    *,
    default: int = 0,
) -> int:
    try:
        return int(float(value))
    except (
        TypeError,
        ValueError,
    ):
        return default


def boolean(
    value,
) -> bool:
    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {
        "true",
        "1",
        "yes",
    }


def text(
    value,
) -> str:
    if value is None:
        return ""

    return str(value)
