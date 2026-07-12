"""Research candidate enrichment."""

from __future__ import annotations

import pandas as pd

from atlas.investment.research_candidate_consolidator.identity import (
    extract_condition_value,
    extract_feature_name,
    feature_family,
    text,
)


ENRICHED_COLUMNS = [
    "candidate_id",
    "candidate_type",
    "title",
    "parent_engine_id",
    "engine_family",
    "final_priority_score",
    "priority_band",
    "recommendation",
    "rank_eligible",
    "feature_name",
    "feature_family",
    "condition_value",
    "research_signature",
    "execution_authorized",
    "execution_instruction",
]


def enrich_candidates(
    priority_queue: pd.DataFrame,
) -> pd.DataFrame:
    """Add consolidation dimensions to ranked candidates."""
    if (
        priority_queue is None
        or priority_queue.empty
    ):
        return pd.DataFrame(
            columns=ENRICHED_COLUMNS
        )

    rows = []

    for _, row in (
        priority_queue.iterrows()
    ):
        title = text(
            row.get("title")
        )

        engine_id = text(
            row.get(
                "parent_engine_id"
            )
        )

        feature = extract_feature_name(
            title
        )

        family = feature_family(
            feature,
            title,
        )

        condition = (
            extract_condition_value(
                title
            )
        )

        signature = "|".join([
            engine_id or "NO_ENGINE",
            family,
            text(
                row.get(
                    "candidate_type"
                )
            ),
        ])

        rows.append({
            "candidate_id": text(
                row.get(
                    "candidate_id"
                )
            ),
            "candidate_type": text(
                row.get(
                    "candidate_type"
                )
            ),
            "title": title,
            "parent_engine_id": (
                engine_id
            ),
            "engine_family": text(
                row.get(
                    "engine_family"
                )
            ),
            "final_priority_score": (
                row.get(
                    "final_priority_score",
                    0.0,
                )
            ),
            "priority_band": text(
                row.get(
                    "priority_band"
                )
            ),
            "recommendation": text(
                row.get(
                    "recommendation"
                )
            ),
            "rank_eligible": bool(
                str(
                    row.get(
                        "rank_eligible"
                    )
                ).lower()
                in {
                    "true",
                    "1",
                }
            ),
            "feature_name": feature,
            "feature_family": family,
            "condition_value": (
                condition
            ),
            "research_signature": (
                signature
            ),
            "execution_authorized": False,
            "execution_instruction": False,
        })

    return pd.DataFrame(
        rows
    )[ENRICHED_COLUMNS]
