"""Persistent snapshot storage and point-in-time resolution."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def upsert_engine_snapshots(
    current: pd.DataFrame,
    path: Path,
) -> pd.DataFrame:
    """Upsert by effective date and engine without fabricating history."""
    existing = safe_read_csv(
        path
    )

    combined = pd.concat(
        [
            existing,
            current,
        ],
        ignore_index=True,
    )

    if combined.empty:
        return combined

    combined["effective_at"] = pd.to_datetime(
        combined["effective_at"],
        errors="coerce",
        utc=True,
    )

    combined = combined.dropna(
        subset=[
            "effective_at",
            "engine_id",
        ]
    ).sort_values(
        [
            "effective_at",
            "captured_at",
            "engine_id",
        ],
        kind="stable",
    ).drop_duplicates(
        subset=[
            "effective_at",
            "engine_id",
        ],
        keep="last",
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    combined.to_csv(
        path,
        index=False,
    )

    return combined.reset_index(
        drop=True
    )


def upsert_context_snapshots(
    current: pd.DataFrame,
    path: Path,
) -> pd.DataFrame:
    """Upsert one global context row per effective date."""
    existing = safe_read_csv(
        path
    )

    combined = pd.concat(
        [
            existing,
            current,
        ],
        ignore_index=True,
    )

    if combined.empty:
        return combined

    combined["effective_at"] = pd.to_datetime(
        combined["effective_at"],
        errors="coerce",
        utc=True,
    )

    combined = combined.dropna(
        subset=["effective_at"]
    ).sort_values(
        [
            "effective_at",
            "captured_at",
        ],
        kind="stable",
    ).drop_duplicates(
        subset=["effective_at"],
        keep="last",
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    combined.to_csv(
        path,
        index=False,
    )

    return combined.reset_index(
        drop=True
    )


def resolve_governance_as_of(
    snapshots: pd.DataFrame,
    as_of: pd.Timestamp,
) -> pd.DataFrame:
    """Resolve the latest complete engine snapshot on or before a date."""
    if (
        snapshots is None
        or snapshots.empty
    ):
        return pd.DataFrame()

    frame = snapshots.copy()

    frame["effective_at"] = pd.to_datetime(
        frame["effective_at"],
        errors="coerce",
        utc=True,
    )

    target = pd.Timestamp(
        as_of
    )

    if target.tzinfo is None:
        target = target.tz_localize(
            "UTC"
        )
    else:
        target = target.tz_convert(
            "UTC"
        )

    eligible_dates = frame.loc[
        frame["effective_at"]
        <= target,
        "effective_at",
    ]

    if eligible_dates.empty:
        return pd.DataFrame()

    effective_at = eligible_dates.max()

    return frame[
        frame["effective_at"]
        == effective_at
    ].copy().reset_index(
        drop=True
    )


def governance_map_as_of(
    snapshots: pd.DataFrame,
    as_of: pd.Timestamp,
) -> dict[str, float]:
    """Return normalized eligible engine weights as of a date."""
    resolved = resolve_governance_as_of(
        snapshots,
        as_of,
    )

    if resolved.empty:
        return {}

    if "eligible" in resolved.columns:
        resolved = resolved[
            resolved[
                "eligible"
            ].astype(str).str.lower().isin(
                [
                    "true",
                    "1",
                    "yes",
                ]
            )
        ]

    if resolved.empty:
        return {}

    resolved[
        "final_governance_weight"
    ] = pd.to_numeric(
        resolved[
            "final_governance_weight"
        ],
        errors="coerce",
    ).fillna(0.0).clip(
        lower=0.0,
    )

    resolved = resolved[
        resolved[
            "final_governance_weight"
        ] > 0
    ]

    total = float(
        resolved[
            "final_governance_weight"
        ].sum()
    )

    if total <= 1e-12:
        return {}

    return {
        str(row["engine_id"]): (
            float(
                row[
                    "final_governance_weight"
                ]
            )
            / total
        )
        for _, row in resolved.iterrows()
    }


def snapshot_coverage(
    snapshots: pd.DataFrame,
) -> dict:
    if snapshots is None or snapshots.empty:
        return {
            "snapshot_dates": 0,
            "engine_rows": 0,
            "first_effective_at": None,
            "last_effective_at": None,
        }

    dates = pd.to_datetime(
        snapshots["effective_at"],
        errors="coerce",
        utc=True,
    ).dropna()

    return {
        "snapshot_dates": int(
            dates.nunique()
        ),
        "engine_rows": int(
            len(snapshots)
        ),
        "first_effective_at": (
            dates.min().isoformat()
            if not dates.empty
            else None
        ),
        "last_effective_at": (
            dates.max().isoformat()
            if not dates.empty
            else None
        ),
    }


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
    ):
        return pd.DataFrame()
