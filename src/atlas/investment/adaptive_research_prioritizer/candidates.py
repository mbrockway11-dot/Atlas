"""Adaptive Research Prioritizer candidate construction."""

from __future__ import annotations

from typing import Any

import pandas as pd

from atlas.investment.adaptive_research_prioritizer.utils import (
    candidate_id,
    first_value,
    text,
)


CANDIDATE_COLUMNS = [
    "candidate_id",
    "natural_key",
    "candidate_type",
    "title",
    "description",
    "hypothesis_id",
    "parent_engine_id",
    "engine_family",
    "failure_mode",
    "proposed_gate",
    "source_priority",
    "source_name",
    "source_row",
    "evidence_hash",
    "execution_instruction",
]


def build_research_candidates(
    sources: dict[str, Any],
) -> pd.DataFrame:
    """Build canonical candidates from research evidence."""
    rows: list[dict] = []

    add_priority_candidates(
        sources.get(
            "research_priorities",
            pd.DataFrame(),
        ),
        rows,
    )

    add_hypothesis_candidates(
        sources.get(
            "hypothesis_library",
            pd.DataFrame(),
        ),
        rows,
    )

    add_failure_mode_candidates(
        sources.get(
            "failure_modes",
            pd.DataFrame(),
        ),
        rows,
    )

    add_gap_candidates(
        sources.get(
            "family_gaps",
            pd.DataFrame(),
        ),
        rows,
    )

    frame = pd.DataFrame(rows)

    if frame.empty:
        return pd.DataFrame(
            columns=CANDIDATE_COLUMNS
        )

    for column in CANDIDATE_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""

    frame = frame.drop_duplicates(
        subset=["natural_key"],
        keep="first",
    )

    return (
        frame[
            CANDIDATE_COLUMNS
        ]
        .sort_values(
            [
                "candidate_type",
                "natural_key",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def add_priority_candidates(
    frame: pd.DataFrame,
    rows: list[dict],
) -> None:
    if frame is None or frame.empty:
        return

    for index, row in frame.iterrows():
        data = row.to_dict()

        title = text(
            first_value(
                data,
                "title",
                "research_priority",
                "priority_name",
                "hypothesis",
                default=(
                    f"Research priority {index}"
                ),
            )
        )

        engine_id = text(
            first_value(
                data,
                "engine_id",
                "parent_engine_id",
            )
        )

        natural_key = text(
            first_value(
                data,
                "priority_id",
                "hypothesis_id",
                default=(
                    f"PRIORITY|{engine_id}|{title}"
                ),
            )
        )

        rows.append(
            candidate_row(
                natural_key=natural_key,
                candidate_type=(
                    "RESEARCH_PRIORITY"
                ),
                title=title,
                description=text(
                    first_value(
                        data,
                        "description",
                        "rationale",
                        "reason",
                    )
                ),
                hypothesis_id=text(
                    data.get(
                        "hypothesis_id"
                    )
                ),
                parent_engine_id=engine_id,
                engine_family=text(
                    first_value(
                        data,
                        "family",
                        "engine_family",
                    )
                ),
                failure_mode=text(
                    data.get(
                        "failure_mode"
                    )
                ),
                proposed_gate=text(
                    first_value(
                        data,
                        "gate_expression",
                        "proposed_gate",
                    )
                ),
                source_priority=source_priority(
                    data
                ),
                source_name=(
                    "research_priorities"
                ),
                source_row=index,
                payload=data,
            )
        )


def add_hypothesis_candidates(
    frame: pd.DataFrame,
    rows: list[dict],
) -> None:
    if frame is None or frame.empty:
        return

    for index, row in frame.iterrows():
        data = row.to_dict()

        hypothesis_id = text(
            first_value(
                data,
                "hypothesis_id",
                "id",
                default=f"HYP-ROW-{index}",
            )
        )

        title = text(
            first_value(
                data,
                "title",
                "hypothesis",
                "name",
                default=hypothesis_id,
            )
        )

        rows.append(
            candidate_row(
                natural_key=hypothesis_id,
                candidate_type="HYPOTHESIS",
                title=title,
                description=text(
                    first_value(
                        data,
                        "description",
                        "rationale",
                        "hypothesis",
                    )
                ),
                hypothesis_id=hypothesis_id,
                parent_engine_id=text(
                    first_value(
                        data,
                        "engine_id",
                        "parent_engine_id",
                    )
                ),
                engine_family=text(
                    first_value(
                        data,
                        "family",
                        "engine_family",
                    )
                ),
                failure_mode=text(
                    data.get(
                        "failure_mode"
                    )
                ),
                proposed_gate=text(
                    first_value(
                        data,
                        "gate_expression",
                        "proposed_gate",
                    )
                ),
                source_priority=source_priority(
                    data
                ),
                source_name=(
                    "hypothesis_library"
                ),
                source_row=index,
                payload=data,
            )
        )


def add_failure_mode_candidates(
    frame: pd.DataFrame,
    rows: list[dict],
) -> None:
    if frame is None or frame.empty:
        return

    for index, row in frame.iterrows():
        data = row.to_dict()

        engine_id = text(
            first_value(
                data,
                "engine_id",
                "parent_engine_id",
            )
        )

        failure_mode = text(
            first_value(
                data,
                "failure_mode",
                "failure_mode_id",
                "failure",
                default=f"FAILURE-{index}",
            )
        )

        title = text(
            first_value(
                data,
                "title",
                "recommended_research",
                default=(
                    f"Investigate {failure_mode}"
                ),
            )
        )

        natural_key = (
            f"FAILURE|{engine_id}|"
            f"{failure_mode}"
        )

        rows.append(
            candidate_row(
                natural_key=natural_key,
                candidate_type=(
                    "FAILURE_MODE_GATE"
                ),
                title=title,
                description=text(
                    first_value(
                        data,
                        "description",
                        "failure_description",
                        "recommended_action",
                    )
                ),
                hypothesis_id=text(
                    data.get(
                        "hypothesis_id"
                    )
                ),
                parent_engine_id=engine_id,
                engine_family=text(
                    first_value(
                        data,
                        "family",
                        "engine_family",
                    )
                ),
                failure_mode=failure_mode,
                proposed_gate=text(
                    first_value(
                        data,
                        "gate_expression",
                        "proposed_gate",
                        "recommended_gate",
                    )
                ),
                source_priority=source_priority(
                    data
                ),
                source_name=(
                    "failure_modes"
                ),
                source_row=index,
                payload=data,
            )
        )


def add_gap_candidates(
    frame: pd.DataFrame,
    rows: list[dict],
) -> None:
    if frame is None or frame.empty:
        return

    for index, row in frame.iterrows():
        data = row.to_dict()

        family = text(
            first_value(
                data,
                "family",
                "engine_family",
                "missing_family",
                default=f"FAMILY-{index}",
            )
        )

        title = text(
            first_value(
                data,
                "title",
                "recommended_research",
                default=(
                    f"Expand {family} research coverage"
                ),
            )
        )

        natural_key = (
            f"FAMILY_GAP|{family}|{title}"
        )

        rows.append(
            candidate_row(
                natural_key=natural_key,
                candidate_type=(
                    "ENGINE_FAMILY_GAP"
                ),
                title=title,
                description=text(
                    first_value(
                        data,
                        "description",
                        "gap_description",
                        "rationale",
                    )
                ),
                hypothesis_id="",
                parent_engine_id=text(
                    data.get(
                        "engine_id"
                    )
                ),
                engine_family=family,
                failure_mode="",
                proposed_gate="",
                source_priority=source_priority(
                    data
                ),
                source_name="family_gaps",
                source_row=index,
                payload=data,
            )
        )


def candidate_row(
    *,
    natural_key: str,
    candidate_type: str,
    title: str,
    description: str,
    hypothesis_id: str,
    parent_engine_id: str,
    engine_family: str,
    failure_mode: str,
    proposed_gate: str,
    source_priority: float,
    source_name: str,
    source_row: int,
    payload: dict,
) -> dict:
    from atlas.investment.adaptive_research_prioritizer.utils import (
        evidence_hash,
    )

    return {
        "candidate_id": candidate_id(
            natural_key
        ),
        "natural_key": natural_key,
        "candidate_type": (
            candidate_type
        ),
        "title": title,
        "description": description,
        "hypothesis_id": hypothesis_id,
        "parent_engine_id": (
            parent_engine_id
        ),
        "engine_family": engine_family,
        "failure_mode": failure_mode,
        "proposed_gate": proposed_gate,
        "source_priority": (
            source_priority
        ),
        "source_name": source_name,
        "source_row": int(
            source_row
        ),
        "evidence_hash": evidence_hash(
            payload
        ),
        "execution_instruction": False,
    }


def source_priority(
    data: dict,
) -> float:
    from atlas.investment.adaptive_research_prioritizer.utils import (
        clamp,
        number,
    )

    raw = first_value(
        data,
        "priority_score",
        "research_priority_score",
        "score",
        "priority",
        default=0.50,
    )

    if isinstance(raw, str):
        mapping = {
            "CRITICAL": 1.0,
            "HIGH": 0.80,
            "MEDIUM": 0.55,
            "LOW": 0.30,
        }

        mapped = mapping.get(
            raw.strip().upper()
        )

        if mapped is not None:
            return mapped

    numeric = number(
        raw,
        default=0.50,
    )

    if numeric > 1.0:
        numeric /= 100.0

    return clamp(numeric)
