"""Research Candidate Consolidator clustering."""

from __future__ import annotations

from collections import defaultdict

import pandas as pd

from atlas.investment.research_candidate_consolidator.config import (
    MIN_PAIR_SIMILARITY,
)
from atlas.investment.research_candidate_consolidator.identity import (
    jaccard_similarity,
    text,
)


class UnionFind:
    """Small deterministic union-find implementation."""

    def __init__(
        self,
        values: list[str],
    ) -> None:
        self.parent = {
            value: value
            for value in values
        }

    def find(
        self,
        value: str,
    ) -> str:
        parent = self.parent[
            value
        ]

        if parent != value:
            self.parent[value] = (
                self.find(parent)
            )

        return self.parent[value]

    def union(
        self,
        left: str,
        right: str,
    ) -> None:
        left_root = self.find(
            left
        )

        right_root = self.find(
            right
        )

        if left_root == right_root:
            return

        first, second = sorted([
            left_root,
            right_root,
        ])

        self.parent[
            second
        ] = first


def build_candidate_clusters(
    candidates: pd.DataFrame,
) -> list[list[str]]:
    """Cluster related candidates by engine and research theme."""
    if (
        candidates is None
        or candidates.empty
    ):
        return []

    eligible = candidates[
        candidates[
            "rank_eligible"
        ].astype(bool)
    ].copy()

    if eligible.empty:
        return []

    candidate_ids = eligible[
        "candidate_id"
    ].astype(str).tolist()

    union_find = UnionFind(
        candidate_ids
    )

    records = eligible.to_dict(
        orient="records"
    )

    for left_index in range(
        len(records)
    ):
        left = records[
            left_index
        ]

        for right_index in range(
            left_index + 1,
            len(records),
        ):
            right = records[
                right_index
            ]

            similarity = candidate_similarity(
                left,
                right,
            )

            if (
                similarity
                >= MIN_PAIR_SIMILARITY
            ):
                union_find.union(
                    text(
                        left[
                            "candidate_id"
                        ]
                    ),
                    text(
                        right[
                            "candidate_id"
                        ]
                    ),
                )

    grouped: dict[
        str,
        list[str],
    ] = defaultdict(list)

    for candidate_id in (
        candidate_ids
    ):
        grouped[
            union_find.find(
                candidate_id
            )
        ].append(candidate_id)

    return [
        sorted(members)
        for _, members in sorted(
            grouped.items()
        )
    ]


def candidate_similarity(
    left: dict,
    right: dict,
) -> float:
    """Score whether two candidates belong to one program."""
    left_engine = text(
        left.get(
            "parent_engine_id"
        )
    )

    right_engine = text(
        right.get(
            "parent_engine_id"
        )
    )

    if (
        left_engine
        and right_engine
        and left_engine
        != right_engine
    ):
        return 0.0

    score = 0.0

    if (
        left_engine
        and left_engine
        == right_engine
    ):
        score += 0.40

    if (
        text(
            left.get(
                "feature_family"
            )
        )
        == text(
            right.get(
                "feature_family"
            )
        )
    ):
        score += 0.25

    if (
        text(
            left.get(
                "candidate_type"
            )
        )
        == text(
            right.get(
                "candidate_type"
            )
        )
    ):
        score += 0.10

    title_similarity = (
        jaccard_similarity(
            left.get("title"),
            right.get("title"),
        )
    )

    score += (
        title_similarity
        * 0.25
    )

    return min(
        1.0,
        score,
    )
