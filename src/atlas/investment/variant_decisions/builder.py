"""Manual Variant Decision Ledger construction."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime

import pandas as pd

from atlas.investment.variant_decisions.config import (
    DEFAULT_IMPLEMENTATION_STATUS,
    DEFAULT_MANUAL_DECISION,
    SCHEMA_VERSION,
    SOURCE,
    VERSION,
)


LEDGER_COLUMNS = [
    "decision_record_id",
    "variant_id",
    "variant_name",
    "hypothesis_id",
    "parent_engine_id",
    "parent_engine_family",
    "feature",
    "target_state",
    "gate_mode",
    "gate_expression",
    "board_rank",
    "board_recommendation",
    "board_score",
    "validation_score",
    "fold_win_rate",
    "candidate_trade_count",
    "retention_ratio",
    "mean_return_advantage",
    "sharpe_advantage",
    "drawdown_improvement",
    "manual_decision",
    "manual_reviewer",
    "manual_rationale",
    "decision_effective_at",
    "decision_recorded_at",
    "approval_version",
    "implementation_status",
    "implementation_owner",
    "implementation_branch",
    "implementation_commit",
    "implementation_started_at",
    "implementation_completed_at",
    "deployment_version",
    "retirement_date",
    "revisit_after",
    "notes",
    "last_board_sync_at",
    "manual_decision_locked",
    "implementation_authorized",
    "production_eligible",
    "execution_instruction",
    "schema_version",
    "source",
]


MANUAL_FIELDS = [
    "manual_decision",
    "manual_reviewer",
    "manual_rationale",
    "decision_effective_at",
    "decision_recorded_at",
    "approval_version",
    "implementation_status",
    "implementation_owner",
    "implementation_branch",
    "implementation_commit",
    "implementation_started_at",
    "implementation_completed_at",
    "deployment_version",
    "retirement_date",
    "revisit_after",
    "notes",
    "manual_decision_locked",
]


def build_current_ledger_rows(
    review_board: pd.DataFrame,
    variant_registry: pd.DataFrame,
) -> pd.DataFrame:
    """Create current ledger candidates from review and registry data."""
    if (
        review_board is None
        or review_board.empty
        or "variant_id"
        not in review_board.columns
    ):
        return pd.DataFrame(
            columns=LEDGER_COLUMNS
        )

    registry_map = build_registry_map(
        variant_registry
    )

    synchronized_at = datetime.now(
        UTC
    ).isoformat()

    rows = []

    for _, board_row in review_board.iterrows():
        variant_id = text(
            board_row.get(
                "variant_id"
            )
        )

        registry_row = registry_map.get(
            variant_id,
            {},
        )

        row = {
            "decision_record_id": (
                build_decision_record_id(
                    variant_id
                )
            ),
            "variant_id": variant_id,
            "variant_name": text(
                board_row.get(
                    "variant_name",
                    registry_row.get(
                        "variant_name",
                        "",
                    ),
                )
            ),
            "hypothesis_id": text(
                board_row.get(
                    "hypothesis_id",
                    registry_row.get(
                        "hypothesis_id",
                        "",
                    ),
                )
            ),
            "parent_engine_id": text(
                board_row.get(
                    "parent_engine_id",
                    registry_row.get(
                        "parent_engine_id",
                        "",
                    ),
                )
            ),
            "parent_engine_family": text(
                board_row.get(
                    "parent_engine_family",
                    registry_row.get(
                        "parent_engine_family",
                        "",
                    ),
                )
            ),
            "feature": text(
                board_row.get(
                    "feature",
                    registry_row.get(
                        "feature",
                        "",
                    ),
                )
            ),
            "target_state": text(
                board_row.get(
                    "target_state",
                    registry_row.get(
                        "target_state",
                        "",
                    ),
                )
            ),
            "gate_mode": text(
                board_row.get(
                    "gate_mode",
                    registry_row.get(
                        "gate_mode",
                        "",
                    ),
                )
            ),
            "gate_expression": text(
                board_row.get(
                    "gate_expression",
                    registry_row.get(
                        "gate_expression",
                        "",
                    ),
                )
            ),
            "board_rank": integer(
                board_row.get(
                    "review_rank"
                )
            ),
            "board_recommendation": text(
                board_row.get(
                    "recommended_decision"
                )
            ).upper(),
            "board_score": number(
                board_row.get(
                    "overall_review_score"
                )
            ),
            "validation_score": number(
                board_row.get(
                    "validation_score"
                )
            ),
            "fold_win_rate": number(
                board_row.get(
                    "fold_win_rate"
                )
            ),
            "candidate_trade_count": integer(
                board_row.get(
                    "candidate_trade_count"
                )
            ),
            "retention_ratio": number(
                board_row.get(
                    "retention_ratio"
                )
            ),
            "mean_return_advantage": number(
                board_row.get(
                    "mean_return_advantage"
                )
            ),
            "sharpe_advantage": number(
                board_row.get(
                    "sharpe_advantage"
                )
            ),
            "drawdown_improvement": number(
                board_row.get(
                    "drawdown_improvement"
                )
            ),
            "manual_decision": (
                DEFAULT_MANUAL_DECISION
            ),
            "manual_reviewer": "",
            "manual_rationale": "",
            "decision_effective_at": "",
            "decision_recorded_at": "",
            "approval_version": "",
            "implementation_status": (
                DEFAULT_IMPLEMENTATION_STATUS
            ),
            "implementation_owner": "",
            "implementation_branch": "",
            "implementation_commit": "",
            "implementation_started_at": "",
            "implementation_completed_at": "",
            "deployment_version": "",
            "retirement_date": "",
            "revisit_after": "",
            "notes": "",
            "last_board_sync_at": (
                synchronized_at
            ),
            "manual_decision_locked": False,
            "implementation_authorized": False,
            "production_eligible": False,
            "execution_instruction": False,
            "schema_version": (
                SCHEMA_VERSION
            ),
            "source": SOURCE,
        }

        rows.append(row)

    return pd.DataFrame(
        rows,
        columns=LEDGER_COLUMNS,
    ).sort_values(
        [
            "board_rank",
            "variant_id",
        ],
        kind="stable",
    ).reset_index(drop=True)


def merge_preserving_manual_decisions(
    existing: pd.DataFrame,
    incoming: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    """Refresh board evidence while preserving all human-controlled fields."""
    if incoming is None or incoming.empty:
        return (
            normalize_ledger(existing),
            {
                "existing_rows": int(
                    len(existing)
                    if existing is not None
                    else 0
                ),
                "incoming_rows": 0,
                "inserted_rows": 0,
                "updated_evidence_rows": 0,
                "preserved_manual_rows": 0,
            },
        )

    existing = normalize_ledger(
        existing
    )

    if existing.empty:
        return (
            incoming.copy(),
            {
                "existing_rows": 0,
                "incoming_rows": int(
                    len(incoming)
                ),
                "inserted_rows": int(
                    len(incoming)
                ),
                "updated_evidence_rows": 0,
                "preserved_manual_rows": 0,
            },
        )

    existing_map = {
        text(row["variant_id"]): (
            row.to_dict()
        )
        for _, row in existing.iterrows()
    }

    merged_rows = []
    inserted = 0
    updated = 0
    preserved = 0

    for _, incoming_row in incoming.iterrows():
        variant_id = text(
            incoming_row["variant_id"]
        )

        current = existing_map.pop(
            variant_id,
            None,
        )

        if current is None:
            merged_rows.append(
                incoming_row.to_dict()
            )
            inserted += 1
            continue

        refreshed = (
            incoming_row.to_dict()
        )

        for field in MANUAL_FIELDS:
            refreshed[field] = current.get(
                field,
                refreshed.get(
                    field,
                    "",
                ),
            )

        refreshed[
            "manual_decision_locked"
        ] = boolean(
            current.get(
                "manual_decision_locked",
                False,
            )
        )

        refreshed[
            "implementation_authorized"
        ] = False

        refreshed[
            "production_eligible"
        ] = False

        refreshed[
            "execution_instruction"
        ] = False

        merged_rows.append(
            refreshed
        )

        updated += 1

        if text(
            current.get(
                "manual_decision"
            )
        ).upper() != DEFAULT_MANUAL_DECISION:
            preserved += 1

    for orphan in existing_map.values():
        merged_rows.append(
            orphan
        )

    merged = pd.DataFrame(
        merged_rows
    )

    for column in LEDGER_COLUMNS:
        if column not in merged.columns:
            merged[column] = ""

    merged = merged[
        LEDGER_COLUMNS
    ].sort_values(
        [
            "board_rank",
            "variant_id",
        ],
        kind="stable",
        na_position="last",
    ).drop_duplicates(
        subset=["variant_id"],
        keep="first",
    ).reset_index(drop=True)

    return (
        merged,
        {
            "existing_rows": int(
                len(existing)
            ),
            "incoming_rows": int(
                len(incoming)
            ),
            "inserted_rows": inserted,
            "updated_evidence_rows": (
                updated
            ),
            "preserved_manual_rows": (
                preserved
            ),
        },
    )


def normalize_ledger(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Restore the canonical ledger schema and writable dtypes."""
    if frame is None or frame.empty:
        return pd.DataFrame(
            columns=LEDGER_COLUMNS
        )

    result = frame.copy()

    for column in LEDGER_COLUMNS:
        if column not in result.columns:
            result[column] = ""

    text_columns = [
        "decision_record_id",
        "variant_id",
        "variant_name",
        "hypothesis_id",
        "parent_engine_id",
        "parent_engine_family",
        "feature",
        "target_state",
        "gate_mode",
        "gate_expression",
        "board_recommendation",
        "manual_decision",
        "manual_reviewer",
        "manual_rationale",
        "decision_effective_at",
        "decision_recorded_at",
        "approval_version",
        "implementation_status",
        "implementation_owner",
        "implementation_branch",
        "implementation_commit",
        "implementation_started_at",
        "implementation_completed_at",
        "deployment_version",
        "retirement_date",
        "revisit_after",
        "notes",
        "last_board_sync_at",
        "schema_version",
        "source",
    ]

    for column in text_columns:
        result[column] = (
            result[column]
            .astype("object")
            .where(
                result[column].notna(),
                "",
            )
        )

    boolean_columns = [
        "manual_decision_locked",
        "implementation_authorized",
        "production_eligible",
        "execution_instruction",
    ]

    for column in boolean_columns:
        result[column] = (
            result[column]
            .apply(boolean)
            .astype(bool)
        )

    return result[
        LEDGER_COLUMNS
    ]

def build_registry_map(
    frame: pd.DataFrame,
) -> dict[str, dict]:
    if (
        frame is None
        or frame.empty
        or "variant_id" not in frame.columns
    ):
        return {}

    return {
        text(
            row["variant_id"]
        ): row.to_dict()
        for _, row in frame.iterrows()
    }


def build_decision_record_id(
    variant_id: str,
) -> str:
    payload = json.dumps(
        {
            "variant_id": variant_id,
            "ledger": VERSION,
        },
        sort_keys=True,
    ).encode("utf-8")

    digest = hashlib.sha256(
        payload
    ).hexdigest()[:16]

    return f"DEC-{digest}"


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


def boolean(
    value,
) -> bool:
    if isinstance(
        value,
        bool,
    ):
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

    if (
        isinstance(value, float)
        and math.isnan(value)
    ):
        return ""

    return str(value)

