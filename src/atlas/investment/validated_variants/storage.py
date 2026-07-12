"""Immutable Validated Variant Registry storage."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


CONFLICT_COLUMNS = [
    "variant_id",
    "existing_hash",
    "incoming_hash",
    "hypothesis_id",
    "conflict_type",
    "resolution",
]


def merge_registry(
    *,
    incoming: pd.DataFrame,
    existing_path: Path,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    dict,
]:
    """Merge without mutating existing immutable specifications."""
    existing = safe_read_csv(
        existing_path
    )

    if existing.empty:
        registry = incoming.copy()

        stats = {
            "existing_rows": 0,
            "incoming_rows": int(
                len(incoming)
            ),
            "inserted_rows": int(
                len(incoming)
            ),
            "unchanged_rows": 0,
            "conflict_rows": 0,
        }

        return (
            registry,
            pd.DataFrame(
                columns=CONFLICT_COLUMNS
            ),
            stats,
        )

    existing_map = {
        str(
            row["variant_id"]
        ): row.to_dict()
        for _, row in existing.iterrows()
    }

    inserted = []
    unchanged = []
    conflicts = []

    for _, incoming_row in incoming.iterrows():
        variant_id = str(
            incoming_row["variant_id"]
        )

        existing_row = existing_map.get(
            variant_id
        )

        if existing_row is None:
            inserted.append(
                incoming_row.to_dict()
            )
            continue

        existing_hash = str(
            existing_row.get(
                "specification_hash",
                "",
            )
        )

        incoming_hash = str(
            incoming_row.get(
                "specification_hash",
                "",
            )
        )

        if existing_hash == incoming_hash:
            unchanged.append(
                variant_id
            )
            continue

        conflicts.append({
            "variant_id": variant_id,
            "existing_hash": (
                existing_hash
            ),
            "incoming_hash": (
                incoming_hash
            ),
            "hypothesis_id": str(
                incoming_row.get(
                    "hypothesis_id",
                    "",
                )
            ),
            "conflict_type": (
                "IMMUTABLE_SPECIFICATION_CHANGED"
            ),
            "resolution": (
                "EXISTING_SPECIFICATION_PRESERVED"
            ),
        })

    new_rows = pd.DataFrame(
        inserted
    )

    registry = pd.concat(
        [
            existing,
            new_rows,
        ],
        ignore_index=True,
    )

    if not registry.empty:
        registry = registry.sort_values(
            [
                "parent_engine_id",
                "variant_id",
            ],
            kind="stable",
        ).drop_duplicates(
            subset=["variant_id"],
            keep="first",
        ).reset_index(drop=True)

    conflict_frame = pd.DataFrame(
        conflicts,
        columns=CONFLICT_COLUMNS,
    )

    stats = {
        "existing_rows": int(
            len(existing)
        ),
        "incoming_rows": int(
            len(incoming)
        ),
        "inserted_rows": int(
            len(inserted)
        ),
        "unchanged_rows": int(
            len(unchanged)
        ),
        "conflict_rows": int(
            len(conflicts)
        ),
    }

    return (
        registry,
        conflict_frame,
        stats,
    )


def write_jsonl(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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

    payload = (
        "\n".join(lines)
        + (
            "\n"
            if lines
            else ""
        )
    )

    path.write_text(
        payload,
        encoding="utf-8",
    )


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
