"""Non-overlapping walk-forward fold construction."""

from __future__ import annotations

import pandas as pd


def assign_walk_forward_folds(
    observations: pd.DataFrame,
    *,
    fold_count: int,
    embargo_days: int,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    """Assign chronological, non-overlapping test folds."""
    if observations is None or observations.empty:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
        )

    ordered = observations.sort_values(
        [
            "timestamp",
            "trade_id",
        ],
        kind="stable",
    ).reset_index(drop=True)

    unique_dates = (
        ordered[
            "timestamp"
        ]
        .dt.normalize()
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    if len(unique_dates) < fold_count:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
        )

    date_chunks = [
        chunk
        for chunk in split_dates(
            unique_dates,
            fold_count,
        )
        if len(chunk) > 0
    ]

    fold_rows = []
    assigned = []

    previous_test_end = None

    for fold_number, dates in enumerate(
        date_chunks,
        start=1,
    ):
        test_start = dates.iloc[0]
        test_end = dates.iloc[-1]

        training_end = (
            test_start
            - pd.Timedelta(
                days=embargo_days,
            )
        )

        test_mask = (
            ordered[
                "timestamp"
            ].dt.normalize().between(
                test_start,
                test_end,
                inclusive="both",
            )
        )

        fold_observations = (
            ordered[
                test_mask
            ].copy()
        )

        fold_observations[
            "fold_number"
        ] = fold_number

        fold_observations[
            "test_start"
        ] = test_start

        fold_observations[
            "test_end"
        ] = test_end

        fold_observations[
            "training_end"
        ] = training_end

        assigned.append(
            fold_observations
        )

        overlap_detected = bool(
            previous_test_end is not None
            and test_start
            <= previous_test_end
        )

        fold_rows.append({
            "fold_number": fold_number,
            "test_start": (
                test_start.isoformat()
            ),
            "test_end": (
                test_end.isoformat()
            ),
            "training_end": (
                training_end.isoformat()
            ),
            "embargo_days": int(
                embargo_days
            ),
            "test_observation_count": int(
                len(
                    fold_observations
                )
            ),
            "overlap_detected": (
                overlap_detected
            ),
            "uses_future_data": False,
        })

        previous_test_end = test_end

    assigned_frame = pd.concat(
        assigned,
        ignore_index=True,
    )

    return (
        assigned_frame,
        pd.DataFrame(
            fold_rows
        ),
    )


def split_dates(
    dates: pd.Series,
    fold_count: int,
) -> list[pd.Series]:
    size = len(dates)
    base = size // fold_count
    remainder = size % fold_count

    chunks = []
    start = 0

    for index in range(
        fold_count
    ):
        width = (
            base
            + (
                1
                if index < remainder
                else 0
            )
        )

        stop = start + width

        chunks.append(
            dates.iloc[
                start:stop
            ]
        )

        start = stop

    return chunks
