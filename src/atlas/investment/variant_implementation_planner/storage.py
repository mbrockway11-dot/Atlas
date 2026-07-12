"""Immutable implementation-plan storage."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def merge_plans(
    existing: pd.DataFrame,
    incoming: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    dict,
]:
    """Preserve existing plans and detect immutable specification changes."""
    if existing is None or existing.empty:
        return (
            incoming.copy(),
            pd.DataFrame(),
            {
                "existing_rows": 0,
                "incoming_rows": int(
                    len(incoming)
                ),
                "inserted_rows": int(
                    len(incoming)
                ),
                "unchanged_rows": 0,
                "conflict_rows": 0,
            },
        )

    existing_map = {
        str(
            row["variant_id"]
        ): row.to_dict()
        for _, row in existing.iterrows()
    }

    merged_rows = []
    conflicts = []
    inserted = 0
    unchanged = 0

    for _, incoming_row in (
        incoming.iterrows()
    ):
        variant_id = str(
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

        if (
            str(
                current.get(
                    "specification_hash",
                    "",
                )
            )
            != str(
                incoming_row.get(
                    "specification_hash",
                    "",
                )
            )
        ):
            conflicts.append({
                "variant_id": (
                    variant_id
                ),
                "existing_hash": current.get(
                    "specification_hash",
                    "",
                ),
                "incoming_hash": (
                    incoming_row.get(
                        "specification_hash",
                        "",
                    )
                ),
                "conflict_type": (
                    "IMPLEMENTATION_SPECIFICATION_CHANGED"
                ),
                "resolution": (
                    "EXISTING_PLAN_PRESERVED"
                ),
            })

        else:
            unchanged += 1

        merged_rows.append(
            current
        )

    merged_rows.extend(
        existing_map.values()
    )

    merged = pd.DataFrame(
        merged_rows
    ).sort_values(
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
        pd.DataFrame(conflicts),
        {
            "existing_rows": int(
                len(existing)
            ),
            "incoming_rows": int(
                len(incoming)
            ),
            "inserted_rows": inserted,
            "unchanged_rows": unchanged,
            "conflict_rows": int(
                len(conflicts)
            ),
        },
    )


def write_jsonl(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    lines = [
        json.dumps(
            row,
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
        for row in frame.to_dict(
            orient="records"
        )
    ]

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        "\n".join(lines)
        + (
            "\n"
            if lines
            else ""
        ),
        encoding="utf-8",
    )
