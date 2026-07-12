"""Research Program Manager registry construction."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd

from atlas.investment.research_program_manager.config import (
    DEFAULT_REVIEW_AFTER_DAYS,
    SCHEMA_VERSION,
    SOURCE,
)
from atlas.investment.research_program_manager.identity import (
    boolean,
    evidence_id,
    number,
    text,
    utc_now,
)


REGISTRY_COLUMNS = [
    "research_program_id",
    "program_rank",
    "program_title",
    "program_theme",
    "parent_engine_id",
    "engine_family",
    "member_count",
    "dimension_count",
    "condition_count",
    "program_priority_score",
    "cluster_confidence",
    "priority_band",
    "prioritizer_recommendation",
    "current_status",
    "status_locked",
    "program_owner",
    "reviewer",
    "decision_rationale",
    "approval_version",
    "created_at",
    "updated_at",
    "review_after",
    "last_evidence_at",
    "evidence_count",
    "dependency_count",
    "blocking_dependency_count",
    "has_conflicts",
    "is_blocked",
    "is_stale",
    "promotion_ready",
    "implementation_authorized",
    "production_eligible",
    "execution_instruction",
    "state_hash",
    "schema_version",
    "source",
]


def build_program_registry(
    *,
    consolidated_programs: pd.DataFrame,
    existing_registry: pd.DataFrame,
    state_hash: str,
) -> pd.DataFrame:
    """Reconcile current consolidated programs with preserved governance."""
    now = datetime.now(
        UTC
    )

    now_text = now.isoformat()

    review_after = (
        now
        + timedelta(
            days=DEFAULT_REVIEW_AFTER_DAYS
        )
    ).isoformat()

    existing_map = {}

    if (
        existing_registry is not None
        and not existing_registry.empty
    ):
        existing_map = {
            text(
                row.get(
                    "research_program_id"
                )
            ): row.to_dict()
            for _, row in (
                existing_registry.iterrows()
            )
        }

    rows = []

    if (
        consolidated_programs is None
        or consolidated_programs.empty
    ):
        return pd.DataFrame(
            columns=REGISTRY_COLUMNS
        )

    for _, row in (
        consolidated_programs.iterrows()
    ):
        source = row.to_dict()

        program_id = text(
            source.get(
                "research_program_id"
            )
        )

        previous = existing_map.get(
            program_id,
            {},
        )

        preserved_status = text(
            previous.get(
                "current_status"
            )
        )

        current_status = (
            preserved_status
            if preserved_status
            else "PROPOSED"
        )

        created_at = text(
            previous.get(
                "created_at"
            )
        ) or now_text

        rows.append({
            "research_program_id": (
                program_id
            ),
            "program_rank": source.get(
                "program_rank",
                0,
            ),
            "program_title": text(
                source.get(
                    "program_title"
                )
            ),
            "program_theme": text(
                source.get(
                    "program_theme"
                )
            ),
            "parent_engine_id": text(
                source.get(
                    "parent_engine_id"
                )
            ),
            "engine_family": text(
                source.get(
                    "engine_family"
                )
            ),
            "member_count": source.get(
                "member_count",
                0,
            ),
            "dimension_count": source.get(
                "dimension_count",
                0,
            ),
            "condition_count": source.get(
                "condition_count",
                0,
            ),
            "program_priority_score": (
                source.get(
                    "program_priority_score",
                    0.0,
                )
            ),
            "cluster_confidence": (
                source.get(
                    "cluster_confidence",
                    0.0,
                )
            ),
            "priority_band": text(
                source.get(
                    "priority_band"
                )
            ),
            "prioritizer_recommendation": text(
                source.get(
                    "recommendation"
                )
            ),
            "current_status": (
                current_status
            ),
            "status_locked": boolean(
                previous.get(
                    "status_locked",
                    False,
                )
            ),
            "program_owner": text(
                previous.get(
                    "program_owner"
                )
            ),
            "reviewer": text(
                previous.get(
                    "reviewer"
                )
            ),
            "decision_rationale": text(
                previous.get(
                    "decision_rationale"
                )
            ),
            "approval_version": text(
                previous.get(
                    "approval_version"
                )
            ),
            "created_at": created_at,
            "updated_at": now_text,
            "review_after": text(
                previous.get(
                    "review_after"
                )
            ) or review_after,
            "last_evidence_at": text(
                previous.get(
                    "last_evidence_at"
                )
            ),
            "evidence_count": previous.get(
                "evidence_count",
                0,
            ),
            "dependency_count": previous.get(
                "dependency_count",
                0,
            ),
            "blocking_dependency_count": (
                previous.get(
                    "blocking_dependency_count",
                    0,
                )
            ),
            "has_conflicts": boolean(
                source.get(
                    "has_conflicts"
                )
            ),
            "is_blocked": boolean(
                previous.get(
                    "is_blocked",
                    False,
                )
            ),
            "is_stale": False,
            "promotion_ready": False,
            "implementation_authorized": False,
            "production_eligible": False,
            "execution_instruction": False,
            "state_hash": state_hash,
            "schema_version": (
                SCHEMA_VERSION
            ),
            "source": SOURCE,
        })

    frame = pd.DataFrame(
        rows
    )

    for column in REGISTRY_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""

    return frame[
        REGISTRY_COLUMNS
    ]


def build_program_evidence(
    *,
    registry: pd.DataFrame,
    members: pd.DataFrame,
    dimensions: pd.DataFrame,
    conflicts: pd.DataFrame,
    state_hash: str,
) -> pd.DataFrame:
    """Build deterministic evidence records from program inputs."""
    rows = []

    if registry is None or registry.empty:
        return pd.DataFrame()

    for _, program in (
        registry.iterrows()
    ):
        program_id = text(
            program.get(
                "research_program_id"
            )
        )

        program_members = filter_program(
            members,
            program_id,
        )

        program_dimensions = filter_program(
            dimensions,
            program_id,
        )

        program_conflicts = filter_program(
            conflicts,
            program_id,
        )

        summary_payload = {
            "member_count": int(
                len(program_members)
            ),
            "dimension_count": int(
                len(program_dimensions)
            ),
            "conflict_count": int(
                len(program_conflicts)
            ),
            "priority_score": number(
                program.get(
                    "program_priority_score"
                )
            ),
            "cluster_confidence": number(
                program.get(
                    "cluster_confidence"
                )
            ),
        }

        rows.append({
            "evidence_id": evidence_id(
                program_id=program_id,
                evidence_type=(
                    "CONSOLIDATION_SUMMARY"
                ),
                source_key=program_id,
                payload=summary_payload,
            ),
            "research_program_id": (
                program_id
            ),
            "evidence_type": (
                "CONSOLIDATION_SUMMARY"
            ),
            "source_record_key": (
                program_id
            ),
            "evidence_status": (
                "CURRENT"
            ),
            "evidence_score": number(
                program.get(
                    "program_priority_score"
                )
            ),
            "confidence_score": number(
                program.get(
                    "cluster_confidence"
                )
            ),
            "summary": (
                f"{len(program_members)} candidate(s), "
                f"{len(program_dimensions)} dimension(s), "
                f"{len(program_conflicts)} conflict(s)."
            ),
            "observed_at": utc_now(),
            "state_hash": state_hash,
            "execution_instruction": False,
        })

        for _, member in (
            program_members.iterrows()
        ):
            candidate_id = text(
                member.get(
                    "candidate_id"
                )
            )

            payload = member.to_dict()

            rows.append({
                "evidence_id": evidence_id(
                    program_id=program_id,
                    evidence_type=(
                        "CANDIDATE_MEMBER"
                    ),
                    source_key=candidate_id,
                    payload=payload,
                ),
                "research_program_id": (
                    program_id
                ),
                "evidence_type": (
                    "CANDIDATE_MEMBER"
                ),
                "source_record_key": (
                    candidate_id
                ),
                "evidence_status": (
                    "CURRENT"
                ),
                "evidence_score": number(
                    member.get(
                        "candidate_score"
                    )
                ),
                "confidence_score": number(
                    program.get(
                        "cluster_confidence"
                    )
                ),
                "summary": text(
                    member.get(
                        "candidate_title"
                    )
                ),
                "observed_at": utc_now(),
                "state_hash": state_hash,
                "execution_instruction": False,
            })

    return (
        pd.DataFrame(rows)
        .drop_duplicates(
            subset=["evidence_id"],
            keep="first",
        )
        .reset_index(drop=True)
    )


def filter_program(
    frame: pd.DataFrame,
    program_id: str,
) -> pd.DataFrame:
    if (
        frame is None
        or frame.empty
        or "research_program_id"
        not in frame.columns
    ):
        return pd.DataFrame()

    return frame[
        frame[
            "research_program_id"
        ].astype(str).eq(
            program_id
        )
    ].copy()
