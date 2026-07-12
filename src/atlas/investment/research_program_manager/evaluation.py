"""Research Program Manager dependency and queue evaluation."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from atlas.investment.research_program_manager.config import (
    ACTIVE_STATUSES,
    PROMOTION_CONFIDENCE_THRESHOLD,
    PROMOTION_SCORE_THRESHOLD,
    STALE_ACTIVE_AFTER_DAYS,
)
from atlas.investment.research_program_manager.identity import (
    dependency_id,
    number,
    text,
)


def build_program_dependencies(
    *,
    registry: pd.DataFrame,
    members: pd.DataFrame,
    conflicts: pd.DataFrame,
) -> pd.DataFrame:
    """Build deterministic program dependency records."""
    rows = []

    if registry is None or registry.empty:
        return pd.DataFrame()

    for _, program in registry.iterrows():
        program_id = text(
            program.get(
                "research_program_id"
            )
        )

        engine_id = text(
            program.get(
                "parent_engine_id"
            )
        )

        if engine_id:
            rows.append({
                "dependency_id": (
                    dependency_id(
                        program_id=program_id,
                        dependency_type=(
                            "PARENT_ENGINE"
                        ),
                        dependency_key=engine_id,
                    )
                ),
                "research_program_id": (
                    program_id
                ),
                "dependency_type": (
                    "PARENT_ENGINE"
                ),
                "dependency_key": (
                    engine_id
                ),
                "dependency_status": (
                    "AVAILABLE"
                ),
                "blocking": False,
                "reason": "",
                "execution_instruction": False,
            })
        else:
            rows.append({
                "dependency_id": (
                    dependency_id(
                        program_id=program_id,
                        dependency_type=(
                            "PARENT_ENGINE"
                        ),
                        dependency_key=(
                            "MISSING"
                        ),
                    )
                ),
                "research_program_id": (
                    program_id
                ),
                "dependency_type": (
                    "PARENT_ENGINE"
                ),
                "dependency_key": "",
                "dependency_status": (
                    "MISSING"
                ),
                "blocking": True,
                "reason": (
                    "Program has no resolved parent engine."
                ),
                "execution_instruction": False,
            })

        program_conflicts = filter_program(
            conflicts,
            program_id,
        )

        if not program_conflicts.empty:
            rows.append({
                "dependency_id": (
                    dependency_id(
                        program_id=program_id,
                        dependency_type=(
                            "CONFLICT_RESOLUTION"
                        ),
                        dependency_key=(
                            "PROGRAM_CONFLICTS"
                        ),
                    )
                ),
                "research_program_id": (
                    program_id
                ),
                "dependency_type": (
                    "CONFLICT_RESOLUTION"
                ),
                "dependency_key": (
                    "PROGRAM_CONFLICTS"
                ),
                "dependency_status": (
                    "UNRESOLVED"
                ),
                "blocking": True,
                "reason": (
                    f"{len(program_conflicts)} "
                    "candidate-condition conflict(s) "
                    "require review."
                ),
                "execution_instruction": False,
            })

    return (
        pd.DataFrame(rows)
        .drop_duplicates(
            subset=["dependency_id"],
            keep="first",
        )
        .reset_index(drop=True)
    )


def evaluate_program_state(
    *,
    registry: pd.DataFrame,
    evidence: pd.DataFrame,
    dependencies: pd.DataFrame,
) -> pd.DataFrame:
    """Derive blockers, staleness, and promotion readiness."""
    if registry is None or registry.empty:
        return registry

    result = registry.copy()

    now = datetime.now(
        UTC
    )

    for index, row in (
        result.iterrows()
    ):
        program_id = text(
            row.get(
                "research_program_id"
            )
        )

        program_evidence = filter_program(
            evidence,
            program_id,
        )

        program_dependencies = (
            filter_program(
                dependencies,
                program_id,
            )
        )

        blocking_count = 0

        if not program_dependencies.empty:
            blocking_count = int(
                program_dependencies[
                    "blocking"
                ].astype(bool).sum()
            )

        evidence_count = int(
            len(program_evidence)
        )

        last_evidence_at = ""

        if (
            not program_evidence.empty
            and "observed_at"
            in program_evidence.columns
        ):
            timestamps = pd.to_datetime(
                program_evidence[
                    "observed_at"
                ],
                utc=True,
                errors="coerce",
            ).dropna()

            if not timestamps.empty:
                last_evidence_at = (
                    timestamps.max().isoformat()
                )

        updated_at = pd.to_datetime(
            row.get(
                "updated_at"
            ),
            utc=True,
            errors="coerce",
        )

        age_days = 0.0

        if not pd.isna(updated_at):
            age_days = (
                now - updated_at
            ).total_seconds() / 86400.0

        status = text(
            row.get(
                "current_status"
            )
        )

        is_stale = bool(
            status in ACTIVE_STATUSES
            and age_days
            > STALE_ACTIVE_AFTER_DAYS
        )

        score = number(
            row.get(
                "program_priority_score"
            )
        )

        confidence = number(
            row.get(
                "cluster_confidence"
            )
        )

        promotion_ready = bool(
            status
            == "EVIDENCE_ACCUMULATING"
            and blocking_count == 0
            and score
            >= PROMOTION_SCORE_THRESHOLD
            and confidence
            >= PROMOTION_CONFIDENCE_THRESHOLD
            and evidence_count > 0
        )

        result.at[
            index,
            "evidence_count",
        ] = evidence_count

        result.at[
            index,
            "dependency_count",
        ] = len(
            program_dependencies
        )

        result.at[
            index,
            "blocking_dependency_count",
        ] = blocking_count

        result.at[
            index,
            "last_evidence_at",
        ] = last_evidence_at

        result.at[
            index,
            "is_blocked",
        ] = blocking_count > 0

        result.at[
            index,
            "is_stale",
        ] = is_stale

        result.at[
            index,
            "promotion_ready",
        ] = promotion_ready

        result.at[
            index,
            "implementation_authorized",
        ] = False

        result.at[
            index,
            "production_eligible",
        ] = False

        result.at[
            index,
            "execution_instruction",
        ] = False

    return result


def build_program_queues(
    registry: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Build lifecycle-specific management queues."""
    if registry is None or registry.empty:
        empty = pd.DataFrame()

        return {
            "approval": empty,
            "active": empty,
            "blocked": empty,
            "promotion": empty,
            "archived": empty,
        }

    approval = registry[
        registry[
            "current_status"
        ].astype(str).eq(
            "PROPOSED"
        )
    ].copy()

    active = registry[
        registry[
            "current_status"
        ].astype(str).isin(
            ACTIVE_STATUSES
        )
    ].copy()

    blocked = registry[
        registry[
            "is_blocked"
        ].astype(bool)
    ].copy()

    promotion = registry[
        registry[
            "promotion_ready"
        ].astype(bool)
    ].copy()

    archived = registry[
        registry[
            "current_status"
        ].astype(str).isin({
            "PROMOTED",
            "REJECTED",
            "ARCHIVED",
        })
    ].copy()

    for frame in (
        approval,
        active,
        blocked,
        promotion,
        archived,
    ):
        if not frame.empty:
            frame.sort_values(
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
                inplace=True,
            )

            frame.reset_index(
                drop=True,
                inplace=True,
            )

    return {
        "approval": approval,
        "active": active,
        "blocked": blocked,
        "promotion": promotion,
        "archived": archived,
    }


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
