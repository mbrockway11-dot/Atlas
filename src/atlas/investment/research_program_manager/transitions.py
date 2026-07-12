"""Research Program Manager lifecycle transitions."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd

from atlas.investment.research_program_manager.identity import (
    history_id,
    normalize_status,
    text,
    utc_now,
    validate_transition,
)


TEXT_COLUMNS = [
    "current_status",
    "program_owner",
    "reviewer",
    "decision_rationale",
    "approval_version",
    "review_after",
    "updated_at",
]


def ensure_registry_dtypes(
    registry: pd.DataFrame,
) -> pd.DataFrame:
    """Ensure manually editable text columns accept strings."""
    result = registry.copy()

    for column in TEXT_COLUMNS:
        if column not in result.columns:
            result[column] = ""

        result[column] = (
            result[column]
            .fillna("")
            .astype("object")
        )

    return result


def record_program_transition(
    *,
    registry: pd.DataFrame,
    history: pd.DataFrame,
    program_id: str,
    new_status: str,
    reviewer: str,
    rationale: str,
    approval_version: str = "",
    program_owner: str = "",
    review_after: str = "",
    notes: str = "",
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
]:
    """Record one explicit human-governed lifecycle transition."""
    if registry is None or registry.empty:
        raise ValueError(
            "Research program registry is empty."
        )

    result = ensure_registry_dtypes(
        registry
    )

    matching = result[
        result[
            "research_program_id"
        ].astype(str).eq(
            str(program_id)
        )
    ]

    if matching.empty:
        raise ValueError(
            f"Unknown research program: {program_id}"
        )

    index = matching.index[0]

    previous_status = normalize_status(
        result.at[
            index,
            "current_status",
        ]
    )

    target_status = normalize_status(
        new_status
    )

    validate_transition(
        previous_status,
        target_status,
    )

    recorded_at = utc_now()

    result.at[
        index,
        "current_status",
    ] = target_status

    result.at[
        index,
        "reviewer",
    ] = text(reviewer).strip()

    result.at[
        index,
        "decision_rationale",
    ] = text(rationale).strip()

    result.at[
        index,
        "approval_version",
    ] = text(
        approval_version
    ).strip()

    result.at[
        index,
        "updated_at",
    ] = recorded_at

    result.at[
        index,
        "status_locked",
    ] = True

    if text(program_owner):
        result.at[
            index,
            "program_owner",
        ] = text(
            program_owner
        ).strip()

    if text(review_after):
        result.at[
            index,
            "review_after",
        ] = text(
            review_after
        ).strip()

    history_row = {
        "history_id": history_id(
            program_id=program_id,
            previous_status=(
                previous_status
            ),
            new_status=target_status,
            reviewer=text(reviewer),
            recorded_at=recorded_at,
        ),
        "research_program_id": (
            program_id
        ),
        "previous_status": (
            previous_status
        ),
        "new_status": target_status,
        "reviewer": text(reviewer),
        "rationale": text(rationale),
        "approval_version": text(
            approval_version
        ),
        "program_owner": text(
            program_owner
        ),
        "review_after": text(
            review_after
        ),
        "notes": text(notes),
        "recorded_at": recorded_at,
        "execution_instruction": False,
    }

    history_result = pd.concat(
        [
            (
                history
                if history is not None
                else pd.DataFrame()
            ),
            pd.DataFrame([
                history_row
            ]),
        ],
        ignore_index=True,
    )

    history_result = (
        history_result.drop_duplicates(
            subset=["history_id"],
            keep="first",
        )
        .reset_index(drop=True)
    )

    return (
        result,
        history_result,
        history_row,
    )
