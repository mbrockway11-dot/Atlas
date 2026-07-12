"""Adaptive Research Prioritizer queue construction."""

from __future__ import annotations

import pandas as pd


QUEUE_COLUMNS = [
    "priority_rank",
    "candidate_id",
    "candidate_type",
    "title",
    "parent_engine_id",
    "engine_family",
    "final_priority_score",
    "priority_band",
    "recommendation",
    "rank_eligible",
    "research_action",
    "approval_required",
    "execution_authorized",
    "execution_instruction",
]


def build_priority_queue(
    scores: pd.DataFrame,
) -> pd.DataFrame:
    """Build the final advisory priority queue."""
    if scores is None or scores.empty:
        return pd.DataFrame(
            columns=QUEUE_COLUMNS
        )

    queue = scores.copy()

    queue[
        "research_action"
    ] = queue.apply(
        build_research_action,
        axis=1,
    )

    queue[
        "approval_required"
    ] = True

    queue[
        "execution_authorized"
    ] = False

    queue[
        "execution_instruction"
    ] = False

    queue = queue.sort_values(
        [
            "rank_eligible",
            "final_priority_score",
            "candidate_id",
        ],
        ascending=[
            False,
            False,
            True,
        ],
        kind="stable",
    ).reset_index(drop=True)

    queue.insert(
        0,
        "priority_rank",
        range(
            1,
            len(queue) + 1,
        ),
    )

    return queue[
        QUEUE_COLUMNS
    ]


def build_explanations(
    scores: pd.DataFrame,
) -> pd.DataFrame:
    """Produce one human-readable explanation per candidate."""
    if scores is None or scores.empty:
        return pd.DataFrame()

    rows = []

    for _, row in scores.iterrows():
        drivers = sorted(
            [
                (
                    "source priority",
                    float(
                        row[
                            "source_priority_score"
                        ]
                    ),
                ),
                (
                    "failure recurrence",
                    float(
                        row[
                            "failure_recurrence_score"
                        ]
                    ),
                ),
                (
                    "coverage gap",
                    float(
                        row[
                            "coverage_gap_score"
                        ]
                    ),
                ),
                (
                    "graph importance",
                    float(
                        row[
                            "graph_importance_score"
                        ]
                    ),
                ),
                (
                    "validation potential",
                    float(
                        row[
                            "validation_potential_score"
                        ]
                    ),
                ),
                (
                    "regime relevance",
                    float(
                        row[
                            "regime_relevance_score"
                        ]
                    ),
                ),
                (
                    "novelty",
                    float(
                        row[
                            "novelty_score"
                        ]
                    ),
                ),
            ],
            key=lambda item: item[1],
            reverse=True,
        )

        top_drivers = drivers[:3]

        explanation = (
            f"Ranked {row['priority_band']} with score "
            f"{float(row['final_priority_score']):.4f}. "
            "Primary drivers: "
            + ", ".join(
                f"{name}={value:.2f}"
                for name, value
                in top_drivers
            )
            + "."
        )

        if (
            float(
                row[
                    "duplication_penalty"
                ]
            )
            > 0
        ):
            explanation += (
                " The score includes a duplication "
                f"penalty of "
                f"{float(row['duplication_penalty']):.2f}."
            )

        if not bool(
            row[
                "rank_eligible"
            ]
        ):
            explanation += (
                " The candidate is not rank-eligible "
                "because materially equivalent research "
                "already exists."
            )

        rows.append({
            "candidate_id": row[
                "candidate_id"
            ],
            "title": row["title"],
            "priority_band": row[
                "priority_band"
            ],
            "recommendation": row[
                "recommendation"
            ],
            "explanation": (
                explanation
            ),
            "execution_instruction": False,
        })

    return pd.DataFrame(rows)


def build_research_action(
    row: pd.Series,
) -> str:
    candidate_type = str(
        row[
            "candidate_type"
        ]
    )

    recommendation = str(
        row["recommendation"]
    )

    action_map = {
        "FAILURE_MODE_GATE": (
            "Reconstruct and walk-forward test "
            "the proposed gated engine variant."
        ),
        "HYPOTHESIS": (
            "Run non-overlapping walk-forward "
            "hypothesis validation."
        ),
        "ENGINE_FAMILY_GAP": (
            "Design a research-only prototype "
            "for the underrepresented engine family."
        ),
        "RESEARCH_PRIORITY": (
            "Convert the priority into a versioned "
            "research hypothesis and validation plan."
        ),
    }

    base = action_map.get(
        candidate_type,
        "Prepare a research-only validation plan.",
    )

    return (
        f"{recommendation}: {base}"
    )
