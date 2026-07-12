"""Consolidated research-program construction."""

from __future__ import annotations

from collections import Counter

import pandas as pd

from atlas.investment.research_candidate_consolidator.config import (
    MIN_CLUSTER_CONFIDENCE,
    MIN_CLUSTER_SIZE,
)
from atlas.investment.research_candidate_consolidator.identity import (
    clamp,
    program_id,
    text,
)


PROGRAM_COLUMNS = [
    "program_rank",
    "research_program_id",
    "program_title",
    "program_theme",
    "parent_engine_id",
    "engine_family",
    "member_count",
    "dimension_count",
    "condition_count",
    "mean_candidate_score",
    "max_candidate_score",
    "program_priority_score",
    "cluster_confidence",
    "priority_band",
    "recommendation",
    "has_conflicts",
    "approval_required",
    "execution_authorized",
    "execution_instruction",
]


def build_research_programs(
    candidates: pd.DataFrame,
    clusters: list[list[str]],
) -> dict[str, pd.DataFrame]:
    """Build research programs and full membership lineage."""
    lookup = candidates.set_index(
        "candidate_id",
        drop=False,
    )

    program_rows = []
    member_rows = []
    dimension_rows = []
    conflict_rows = []
    unconsolidated_rows = []
    audit_rows = []

    for cluster_index, member_ids in enumerate(
        clusters,
        start=1,
    ):
        existing_ids = [
            member_id
            for member_id in member_ids
            if member_id
            in lookup.index
        ]

        if not existing_ids:
            continue

        members = lookup.loc[
            existing_ids
        ]

        if isinstance(
            members,
            pd.Series,
        ):
            members = members.to_frame().T

        if (
            len(members)
            < MIN_CLUSTER_SIZE
        ):
            for _, member in (
                members.iterrows()
            ):
                unconsolidated_rows.append(
                    member.to_dict()
                )

            continue

        engine_id = dominant_value(
            members[
                "parent_engine_id"
            ]
        )

        engine_family = dominant_value(
            members[
                "engine_family"
            ]
        )

        dimensions = sorted(
            {
                text(value)
                for value in members[
                    "feature_family"
                ]
                if text(value)
            }
        )

        conditions = sorted(
            {
                text(value)
                for value in members[
                    "condition_value"
                ]
                if text(value)
            }
        )

        theme = infer_theme(
            engine_id=engine_id,
            dimensions=dimensions,
        )

        current_program_id = (
            program_id(
                engine_id=engine_id,
                theme=theme,
                member_ids=(
                    existing_ids
                ),
            )
        )

        candidate_scores = (
            members[
                "final_priority_score"
            ].astype(float)
        )

        mean_score = float(
            candidate_scores.mean()
        )

        max_score = float(
            candidate_scores.max()
        )

        confidence = calculate_cluster_confidence(
            members
        )

        conflicts = detect_conflicts(
            members
        )

        breadth_bonus = min(
            0.10,
            len(dimensions)
            * 0.02,
        )

        evidence_bonus = min(
            0.08,
            len(members)
            * 0.005,
        )

        conflict_penalty = min(
            0.12,
            len(conflicts)
            * 0.03,
        )

        program_score = clamp(
            (
                max_score * 0.55
                + mean_score * 0.30
                + confidence * 0.15
                + breadth_bonus
                + evidence_bonus
                - conflict_penalty
            )
        )

        recommendation = (
            "RESEARCH_NOW"
            if program_score >= 0.72
            else "QUEUE"
            if program_score >= 0.55
            else "MONITOR"
        )

        priority_band = (
            "CRITICAL"
            if program_score >= 0.80
            else "HIGH"
            if program_score >= 0.65
            else "MEDIUM"
            if program_score >= 0.45
            else "LOW"
        )

        program_title = (
            build_program_title(
                engine_id=engine_id,
                dimensions=dimensions,
            )
        )

        program_rows.append({
            "research_program_id": (
                current_program_id
            ),
            "program_title": (
                program_title
            ),
            "program_theme": theme,
            "parent_engine_id": (
                engine_id
            ),
            "engine_family": (
                engine_family
            ),
            "member_count": int(
                len(members)
            ),
            "dimension_count": int(
                len(dimensions)
            ),
            "condition_count": int(
                len(conditions)
            ),
            "mean_candidate_score": round(
                mean_score,
                8,
            ),
            "max_candidate_score": round(
                max_score,
                8,
            ),
            "program_priority_score": round(
                program_score,
                8,
            ),
            "cluster_confidence": round(
                confidence,
                8,
            ),
            "priority_band": (
                priority_band
            ),
            "recommendation": (
                recommendation
            ),
            "has_conflicts": bool(
                conflicts
            ),
            "approval_required": True,
            "execution_authorized": False,
            "execution_instruction": False,
        })

        for member_rank, (
            _,
            member,
        ) in enumerate(
            members.sort_values(
                "final_priority_score",
                ascending=False,
                kind="stable",
            ).iterrows(),
            start=1,
        ):
            member_rows.append({
                "research_program_id": (
                    current_program_id
                ),
                "member_rank": (
                    member_rank
                ),
                "candidate_id": member[
                    "candidate_id"
                ],
                "candidate_title": member[
                    "title"
                ],
                "candidate_type": member[
                    "candidate_type"
                ],
                "feature_name": member[
                    "feature_name"
                ],
                "feature_family": member[
                    "feature_family"
                ],
                "condition_value": member[
                    "condition_value"
                ],
                "candidate_score": member[
                    "final_priority_score"
                ],
                "priority_band": member[
                    "priority_band"
                ],
                "recommendation": member[
                    "recommendation"
                ],
                "execution_instruction": False,
            })

        for dimension in dimensions:
            dimension_members = members[
                members[
                    "feature_family"
                ].astype(str).eq(
                    dimension
                )
            ]

            dimension_rows.append({
                "research_program_id": (
                    current_program_id
                ),
                "dimension": dimension,
                "candidate_count": int(
                    len(
                        dimension_members
                    )
                ),
                "features": "|".join(
                    sorted(
                        {
                            text(value)
                            for value in (
                                dimension_members[
                                    "feature_name"
                                ]
                            )
                            if text(value)
                        }
                    )
                ),
                "conditions": "|".join(
                    sorted(
                        {
                            text(value)
                            for value in (
                                dimension_members[
                                    "condition_value"
                                ]
                            )
                            if text(value)
                        }
                    )
                ),
                "mean_score": round(
                    float(
                        dimension_members[
                            "final_priority_score"
                        ].astype(float).mean()
                    ),
                    8,
                ),
            })

        for conflict in conflicts:
            conflict_rows.append({
                "research_program_id": (
                    current_program_id
                ),
                **conflict,
                "execution_instruction": False,
            })

        audit_rows.append({
            "cluster_index": (
                cluster_index
            ),
            "research_program_id": (
                current_program_id
            ),
            "input_member_count": int(
                len(existing_ids)
            ),
            "accepted": bool(
                confidence
                >= MIN_CLUSTER_CONFIDENCE
            ),
            "cluster_confidence": round(
                confidence,
                8,
            ),
            "reason": (
                "ACCEPTED"
                if confidence
                >= MIN_CLUSTER_CONFIDENCE
                else "LOW_CLUSTER_CONFIDENCE"
            ),
        })

    programs = pd.DataFrame(
        program_rows
    )

    if programs.empty:
        programs = pd.DataFrame(
            columns=PROGRAM_COLUMNS
        )
    else:
        programs = programs.sort_values(
            [
                "program_priority_score",
                "cluster_confidence",
                "research_program_id",
            ],
            ascending=[
                False,
                False,
                True,
            ],
            kind="stable",
        ).reset_index(drop=True)

        programs.insert(
            0,
            "program_rank",
            range(
                1,
                len(programs) + 1,
            ),
        )

        programs = programs[
            PROGRAM_COLUMNS
        ]

    return {
        "programs": programs,
        "members": pd.DataFrame(
            member_rows
        ),
        "dimensions": pd.DataFrame(
            dimension_rows
        ),
        "conflicts": pd.DataFrame(
            conflict_rows
        ),
        "unconsolidated": pd.DataFrame(
            unconsolidated_rows
        ),
        "audit": pd.DataFrame(
            audit_rows
        ),
    }


def dominant_value(
    series: pd.Series,
) -> str:
    values = [
        text(value)
        for value in series
        if text(value)
    ]

    if not values:
        return ""

    return Counter(
        values
    ).most_common(1)[0][0]


def infer_theme(
    *,
    engine_id: str,
    dimensions: list[str],
) -> str:
    dimension_text = (
        "_".join(dimensions)
        if dimensions
        else "general"
    )

    return (
        f"{engine_id}|"
        f"{dimension_text}|"
        "performance_degradation"
    )


def build_program_title(
    *,
    engine_id: str,
    dimensions: list[str],
) -> str:
    readable_engine = (
        engine_id.replace(
            "_",
            " ",
        ).strip()
        or "Atlas engine"
    )

    if not dimensions:
        return (
            f"Investigate {readable_engine} "
            "performance degradation"
        )

    readable_dimensions = ", ".join(
        dimension.replace(
            "_",
            " ",
        )
        for dimension in dimensions
    )

    return (
        f"Investigate {readable_engine} degradation "
        f"across {readable_dimensions} conditions"
    )


def calculate_cluster_confidence(
    members: pd.DataFrame,
) -> float:
    engine_consistency = (
        1.0
        if members[
            "parent_engine_id"
        ].nunique(
            dropna=True
        )
        <= 1
        else 0.40
    )

    candidate_type_consistency = (
        1.0
        / max(
            1,
            members[
                "candidate_type"
            ].nunique(
                dropna=True
            ),
        )
    )

    score_spread = float(
        members[
            "final_priority_score"
        ].astype(float).max()
        - members[
            "final_priority_score"
        ].astype(float).min()
    )

    score_consistency = clamp(
        1.0 - score_spread
    )

    evidence_strength = min(
        1.0,
        len(members) / 8.0,
    )

    return clamp(
        engine_consistency * 0.40
        + candidate_type_consistency * 0.20
        + score_consistency * 0.20
        + evidence_strength * 0.20
    )


def detect_conflicts(
    members: pd.DataFrame,
) -> list[dict]:
    conflicts = []

    grouped = members.groupby(
        "feature_name",
        dropna=False,
    )

    for feature_name, group in grouped:
        feature = text(
            feature_name
        )

        if not feature:
            continue

        conditions = sorted(
            {
                text(value)
                for value in group[
                    "condition_value"
                ]
                if text(value)
            }
        )

        if len(conditions) <= 1:
            continue

        conflicts.append({
            "feature_name": feature,
            "conditions": "|".join(
                conditions
            ),
            "condition_count": int(
                len(conditions)
            ),
            "conflict_type": (
                "MULTIPLE_FAILURE_CONDITIONS"
            ),
            "severity": (
                "HIGH"
                if len(conditions) >= 3
                else "MEDIUM"
            ),
        })

    return conflicts
