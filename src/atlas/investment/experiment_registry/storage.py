"""Append-only Atlas Experiment Registry storage."""

from __future__ import annotations

import pandas as pd


def merge_registry_bundle(
    *,
    existing: dict[str, pd.DataFrame],
    incoming: dict[str, pd.DataFrame],
) -> tuple[
    dict[str, pd.DataFrame],
    dict,
]:
    """Merge incoming evidence without overwriting immutable rows."""
    keys = {
        "experiments": "experiment_id",
        "observations": "observation_id",
        "metrics": "metric_record_id",
        "artifacts": "artifact_record_id",
        "relationships": "relationship_id",
        "statuses": "status_record_id",
        "orchestrator_runs": "run_id",
    }

    merged = {}
    stats = {}

    for name, primary_key in (
        keys.items()
    ):
        previous = existing.get(
            name,
            pd.DataFrame(),
        )

        current = incoming.get(
            name,
            pd.DataFrame(),
        )

        before = len(previous)

        combined = pd.concat(
            [
                previous,
                current,
            ],
            ignore_index=True,
        )

        if (
            primary_key
            in combined.columns
        ):
            combined = (
                combined.drop_duplicates(
                    subset=[
                        primary_key
                    ],
                    keep="first",
                )
            )

        combined = combined.reset_index(
            drop=True
        )

        merged[name] = combined

        stats[name] = {
            "existing_rows": before,
            "incoming_rows": len(
                current
            ),
            "merged_rows": len(
                combined
            ),
            "inserted_rows": max(
                0,
                len(combined) - before,
            ),
        }

    merged[
        "experiments"
    ] = update_experiment_summaries(
        merged["experiments"],
        merged["observations"],
    )

    return merged, stats


def update_experiment_summaries(
    experiments: pd.DataFrame,
    observations: pd.DataFrame,
) -> pd.DataFrame:
    """Refresh derived experiment summary fields only."""
    if (
        experiments.empty
        or observations.empty
    ):
        return experiments

    result = experiments.copy()

    observation_groups = (
        observations.groupby(
            "experiment_id",
            sort=False,
        )
    )

    for experiment_id, group in (
        observation_groups
    ):
        matching = result[
            result[
                "experiment_id"
            ].astype(str).eq(
                str(experiment_id)
            )
        ]

        if matching.empty:
            continue

        index = matching.index[0]

        ordered = group.sort_values(
            "observed_at",
            kind="stable",
        )

        first = ordered.iloc[0]
        latest = ordered.iloc[-1]

        result.at[
            index,
            "first_observed_at",
        ] = first.get(
            "observed_at",
            "",
        )

        result.at[
            index,
            "last_observed_at",
        ] = latest.get(
            "observed_at",
            "",
        )

        result.at[
            index,
            "latest_state_hash",
        ] = latest.get(
            "state_hash",
            "",
        )

        result.at[
            index,
            "latest_source",
        ] = latest.get(
            "source_name",
            "",
        )

        result.at[
            index,
            "current_status",
        ] = latest.get(
            "status",
            result.at[
                index,
                "current_status",
            ],
        )

    return result
