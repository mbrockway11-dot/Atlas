"""Explicit human decision recording."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from atlas.investment.variant_decisions.builder import (
    normalize_ledger,
)
from atlas.investment.variant_decisions.config import (
    ALLOWED_IMPLEMENTATION_STATUSES,
    ALLOWED_MANUAL_DECISIONS,
)


HISTORY_COLUMNS = [
    "history_id",
    "variant_id",
    "previous_decision",
    "new_decision",
    "reviewer",
    "rationale",
    "approval_version",
    "previous_implementation_status",
    "new_implementation_status",
    "revisit_after",
    "notes",
    "recorded_at",
    "execution_instruction",
]


def record_manual_decision(
    *,
    ledger: pd.DataFrame,
    history: pd.DataFrame,
    variant_id: str,
    decision: str,
    reviewer: str,
    rationale: str,
    approval_version: str = "",
    implementation_status: str = "",
    revisit_after: str = "",
    notes: str = "",
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    dict,
]:
    """Record one explicit human decision and append immutable history."""
    normalized_decision = (
        str(decision)
        .strip()
        .upper()
    )

    if (
        normalized_decision
        not in ALLOWED_MANUAL_DECISIONS
    ):
        raise ValueError(
            "Unsupported manual decision: "
            f"{normalized_decision}"
        )

    if not str(reviewer).strip():
        raise ValueError(
            "Reviewer is required."
        )

    if not str(rationale).strip():
        raise ValueError(
            "Rationale is required."
        )

    ledger = normalize_ledger(
        ledger
    )

    matching = ledger[
        ledger["variant_id"]
        .astype(str)
        .eq(str(variant_id))
    ]

    if matching.empty:
        raise ValueError(
            f"Variant not found: {variant_id}"
        )

    index = matching.index[0]

    previous_decision = str(
        ledger.at[
            index,
            "manual_decision",
        ]
    ).upper()

    previous_implementation = str(
        ledger.at[
            index,
            "implementation_status",
        ]
    ).upper()

    resolved_implementation = (
        str(implementation_status)
        .strip()
        .upper()
        if str(
            implementation_status
        ).strip()
        else previous_implementation
    )

    if (
        resolved_implementation
        not in ALLOWED_IMPLEMENTATION_STATUSES
    ):
        raise ValueError(
            "Unsupported implementation status: "
            f"{resolved_implementation}"
        )

    recorded_at = datetime.now(
        UTC
    ).isoformat()

    ledger.at[
        index,
        "manual_decision",
    ] = normalized_decision

    ledger.at[
        index,
        "manual_reviewer",
    ] = str(reviewer).strip()

    ledger.at[
        index,
        "manual_rationale",
    ] = str(rationale).strip()

    ledger.at[
        index,
        "decision_effective_at",
    ] = recorded_at

    ledger.at[
        index,
        "decision_recorded_at",
    ] = recorded_at

    ledger.at[
        index,
        "approval_version",
    ] = str(
        approval_version
    ).strip()

    ledger.at[
        index,
        "implementation_status",
    ] = resolved_implementation

    ledger.at[
        index,
        "revisit_after",
    ] = str(
        revisit_after
    ).strip()

    ledger.at[
        index,
        "notes",
    ] = str(notes).strip()

    ledger.at[
        index,
        "manual_decision_locked",
    ] = True

    ledger.at[
        index,
        "implementation_authorized",
    ] = False

    ledger.at[
        index,
        "production_eligible",
    ] = False

    ledger.at[
        index,
        "execution_instruction",
    ] = False

    history_row = {
        "history_id": build_history_id(
            variant_id=str(
                variant_id
            ),
            decision=(
                normalized_decision
            ),
            reviewer=str(reviewer),
            recorded_at=recorded_at,
        ),
        "variant_id": str(
            variant_id
        ),
        "previous_decision": (
            previous_decision
        ),
        "new_decision": (
            normalized_decision
        ),
        "reviewer": str(
            reviewer
        ).strip(),
        "rationale": str(
            rationale
        ).strip(),
        "approval_version": str(
            approval_version
        ).strip(),
        "previous_implementation_status": (
            previous_implementation
        ),
        "new_implementation_status": (
            resolved_implementation
        ),
        "revisit_after": str(
            revisit_after
        ).strip(),
        "notes": str(notes).strip(),
        "recorded_at": recorded_at,
        "execution_instruction": False,
    }

    history = append_history(
        history,
        history_row,
    )

    return (
        ledger,
        history,
        history_row,
    )


def append_history(
    history: pd.DataFrame,
    row: dict,
) -> pd.DataFrame:
    if history is None:
        history = pd.DataFrame(
            columns=HISTORY_COLUMNS
        )

    result = pd.concat(
        [
            history,
            pd.DataFrame([
                row
            ]),
        ],
        ignore_index=True,
    )

    for column in HISTORY_COLUMNS:
        if column not in result.columns:
            result[column] = ""

    return result[
        HISTORY_COLUMNS
    ].drop_duplicates(
        subset=["history_id"],
        keep="first",
    ).reset_index(drop=True)


def build_history_id(
    *,
    variant_id: str,
    decision: str,
    reviewer: str,
    recorded_at: str,
) -> str:
    payload = json.dumps(
        {
            "variant_id": variant_id,
            "decision": decision,
            "reviewer": reviewer,
            "recorded_at": recorded_at,
        },
        sort_keys=True,
    ).encode("utf-8")

    digest = hashlib.sha256(
        payload
    ).hexdigest()[:20]

    return f"HIST-{digest}"


def safe_read_csv(
    path: Path,
) -> pd.DataFrame:
    if (
        not path.exists()
        or not path.is_file()
        or path.stat().st_size == 0
    ):
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
        OSError,
    ):
        return pd.DataFrame()
