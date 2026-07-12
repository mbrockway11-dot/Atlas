"""Atlas Experiment Registry canonical builders."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd

from atlas.investment.experiment_registry.config import (
    SCHEMA_VERSION,
    SOURCE,
)
from atlas.investment.experiment_registry.identity import (
    build_experiment_id,
    build_observation_id,
    first_value,
    hash_payload,
    integer,
    number,
    text,
)


EXPERIMENT_COLUMNS = [
    "experiment_id",
    "experiment_type",
    "natural_key",
    "title",
    "description",
    "parent_engine_id",
    "engine_family",
    "hypothesis_id",
    "variant_id",
    "portfolio_experiment_id",
    "current_status",
    "created_at",
    "first_observed_at",
    "last_observed_at",
    "latest_state_hash",
    "latest_source",
    "manual_decision",
    "reviewer",
    "production_eligible",
    "execution_instruction",
    "schema_version",
    "source",
]


OBSERVATION_COLUMNS = [
    "observation_id",
    "experiment_id",
    "observed_at",
    "source_name",
    "source_record_key",
    "state_hash",
    "evidence_hash",
    "status",
    "decision",
    "summary",
    "payload_json",
    "execution_instruction",
]


METRIC_COLUMNS = [
    "metric_record_id",
    "observation_id",
    "experiment_id",
    "metric_name",
    "metric_value",
    "metric_text",
    "metric_unit",
    "source_name",
]


RELATIONSHIP_COLUMNS = [
    "relationship_id",
    "from_experiment_id",
    "relationship_type",
    "to_experiment_id",
    "source_name",
    "evidence_hash",
]


def build_registry_bundle(
    sources: dict[str, Any],
) -> dict[str, pd.DataFrame]:
    now = datetime.now(
        UTC
    ).isoformat()

    compiler_hash = text(
        sources.get(
            "compiler_report",
            {},
        ).get(
            "state_hash",
            "",
        )
    )

    experiments: list[dict] = []
    observations: list[dict] = []
    metrics: list[dict] = []
    relationships: list[dict] = []
    artifacts: list[dict] = []
    statuses: list[dict] = []
    orchestrator_runs: list[dict] = []

    hypothesis_map: dict[str, str] = {}
    variant_map: dict[str, str] = {}

    process_hypotheses(
        frame=sources["meta_hypotheses"],
        now=now,
        state_hash=compiler_hash,
        experiments=experiments,
        observations=observations,
        metrics=metrics,
        artifacts=artifacts,
        statuses=statuses,
        hypothesis_map=hypothesis_map,
    )

    process_hypothesis_validation(
        frame=sources["hypothesis_validation"],
        now=now,
        state_hash=compiler_hash,
        experiments=experiments,
        observations=observations,
        metrics=metrics,
        artifacts=artifacts,
        statuses=statuses,
        hypothesis_map=hypothesis_map,
    )

    process_variants(
        sources=sources,
        now=now,
        state_hash=compiler_hash,
        experiments=experiments,
        observations=observations,
        metrics=metrics,
        artifacts=artifacts,
        statuses=statuses,
        relationships=relationships,
        hypothesis_map=hypothesis_map,
        variant_map=variant_map,
    )

    process_portfolio_experiments(
        sources=sources,
        now=now,
        state_hash=compiler_hash,
        experiments=experiments,
        observations=observations,
        metrics=metrics,
        artifacts=artifacts,
        statuses=statuses,
    )

    process_orchestrator_runs(
        frame=sources["orchestrator_history"],
        report=sources["orchestrator_report"],
        now=now,
        state_hash=compiler_hash,
        experiments=experiments,
        observations=observations,
        metrics=metrics,
        artifacts=artifacts,
        statuses=statuses,
        orchestrator_runs=orchestrator_runs,
    )

    return {
        "experiments": frame_from_rows(
            experiments,
            EXPERIMENT_COLUMNS,
        ),
        "observations": frame_from_rows(
            observations,
            OBSERVATION_COLUMNS,
        ),
        "metrics": frame_from_rows(
            metrics,
            METRIC_COLUMNS,
        ),
        "relationships": frame_from_rows(
            relationships,
            RELATIONSHIP_COLUMNS,
        ),
        "artifacts": pd.DataFrame(
            artifacts
        ),
        "statuses": pd.DataFrame(
            statuses
        ),
        "orchestrator_runs": pd.DataFrame(
            orchestrator_runs
        ),
    }


def process_hypotheses(
    *,
    frame: pd.DataFrame,
    now: str,
    state_hash: str,
    experiments: list,
    observations: list,
    metrics: list,
    artifacts: list,
    statuses: list,
    hypothesis_map: dict,
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

        natural_key = hypothesis_id

        experiment_id = (
            build_experiment_id(
                experiment_type="HYPOTHESIS",
                natural_key=natural_key,
            )
        )

        hypothesis_map[
            hypothesis_id
        ] = experiment_id

        title = text(
            first_value(
                data,
                "title",
                "hypothesis",
                "name",
                default=hypothesis_id,
            )
        )

        description = text(
            first_value(
                data,
                "description",
                "rationale",
                "hypothesis",
            )
        )

        status = normalize_status(
            first_value(
                data,
                "status",
                "hypothesis_status",
                default="PROPOSED",
            )
        )

        add_record(
            experiment_id=experiment_id,
            experiment_type="HYPOTHESIS",
            natural_key=natural_key,
            title=title,
            description=description,
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
            hypothesis_id=hypothesis_id,
            variant_id="",
            portfolio_experiment_id="",
            status=status,
            now=now,
            state_hash=state_hash,
            source_name="meta_hypotheses",
            source_record_key=hypothesis_id,
            raw_payload=data,
            experiments=experiments,
            observations=observations,
            metrics=metrics,
            artifacts=artifacts,
            statuses=statuses,
        )


def process_hypothesis_validation(
    *,
    frame: pd.DataFrame,
    now: str,
    state_hash: str,
    experiments: list,
    observations: list,
    metrics: list,
    artifacts: list,
    statuses: list,
    hypothesis_map: dict,
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
                default=f"HYP-VAL-{index}",
            )
        )

        experiment_id = (
            hypothesis_map.get(
                hypothesis_id
            )
            or build_experiment_id(
                experiment_type="HYPOTHESIS",
                natural_key=hypothesis_id,
            )
        )

        hypothesis_map[
            hypothesis_id
        ] = experiment_id

        status = (
            "VALIDATED"
            if validation_passed(data)
            else normalize_status(
                first_value(
                    data,
                    "status",
                    "decision",
                    default="REJECTED",
                )
            )
        )

        add_record(
            experiment_id=experiment_id,
            experiment_type="HYPOTHESIS",
            natural_key=hypothesis_id,
            title=text(
                first_value(
                    data,
                    "title",
                    "hypothesis",
                    default=hypothesis_id,
                )
            ),
            description=text(
                first_value(
                    data,
                    "description",
                    "rationale",
                )
            ),
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
            hypothesis_id=hypothesis_id,
            variant_id="",
            portfolio_experiment_id="",
            status=status,
            now=now,
            state_hash=state_hash,
            source_name=(
                "hypothesis_validation"
            ),
            source_record_key=(
                hypothesis_id
            ),
            raw_payload=data,
            experiments=experiments,
            observations=observations,
            metrics=metrics,
            artifacts=artifacts,
            statuses=statuses,
        )


def process_variants(
    *,
    sources: dict,
    now: str,
    state_hash: str,
    experiments: list,
    observations: list,
    metrics: list,
    artifacts: list,
    statuses: list,
    relationships: list,
    hypothesis_map: dict,
    variant_map: dict,
) -> None:
    variant_sources = [
        (
            "validated_variants",
            sources[
                "validated_variants"
            ],
        ),
        (
            "variant_review",
            sources["variant_review"],
        ),
        (
            "variant_decisions",
            sources[
                "variant_decisions"
            ],
        ),
        (
            "implementation_plans",
            sources[
                "implementation_plans"
            ],
        ),
    ]

    for source_name, frame in (
        variant_sources
    ):
        if frame is None or frame.empty:
            continue

        for index, row in frame.iterrows():
            data = row.to_dict()

            variant_id = text(
                first_value(
                    data,
                    "variant_id",
                    default=(
                        f"VAR-{source_name}-{index}"
                    ),
                )
            )

            experiment_id = (
                variant_map.get(
                    variant_id
                )
                or build_experiment_id(
                    experiment_type=(
                        "VALIDATED_VARIANT"
                    ),
                    natural_key=variant_id,
                )
            )

            variant_map[
                variant_id
            ] = experiment_id

            hypothesis_id = text(
                first_value(
                    data,
                    "hypothesis_id",
                )
            )

            status = infer_variant_status(
                source_name,
                data,
            )

            add_record(
                experiment_id=experiment_id,
                experiment_type=(
                    "VALIDATED_VARIANT"
                ),
                natural_key=variant_id,
                title=text(
                    first_value(
                        data,
                        "variant_name",
                        "title",
                        default=variant_id,
                    )
                ),
                description=text(
                    first_value(
                        data,
                        "gate_expression",
                        "description",
                    )
                ),
                parent_engine_id=text(
                    first_value(
                        data,
                        "parent_engine_id",
                        "engine_id",
                    )
                ),
                engine_family=text(
                    first_value(
                        data,
                        "parent_engine_family",
                        "family",
                    )
                ),
                hypothesis_id=hypothesis_id,
                variant_id=variant_id,
                portfolio_experiment_id="",
                status=status,
                now=now,
                state_hash=state_hash,
                source_name=source_name,
                source_record_key=variant_id,
                raw_payload=data,
                experiments=experiments,
                observations=observations,
                metrics=metrics,
                artifacts=artifacts,
                statuses=statuses,
            )

            if (
                hypothesis_id
                and hypothesis_id
                in hypothesis_map
            ):
                add_relationship(
                    relationships=relationships,
                    from_experiment_id=(
                        hypothesis_map[
                            hypothesis_id
                        ]
                    ),
                    relationship_type=(
                        "GENERATED_VARIANT"
                    ),
                    to_experiment_id=(
                        experiment_id
                    ),
                    source_name=source_name,
                    payload=data,
                )


def process_portfolio_experiments(
    *,
    sources: dict,
    now: str,
    state_hash: str,
    experiments: list,
    observations: list,
    metrics: list,
    artifacts: list,
    statuses: list,
) -> None:
    source_frames = [
        (
            "portfolio_promotion_v1",
            sources[
                "portfolio_promotion_v1"
            ],
        ),
        (
            "portfolio_promotion_v2",
            sources[
                "portfolio_promotion_v2"
            ],
        ),
    ]

    for source_name, frame in source_frames:
        if frame is None or frame.empty:
            continue

        for index, row in frame.iterrows():
            data = row.to_dict()

            natural_key = text(
                first_value(
                    data,
                    "experiment_id",
                    "portfolio_id",
                    "candidate_id",
                    default=(
                        f"{source_name}-{index}"
                    ),
                )
            )

            experiment_id = (
                build_experiment_id(
                    experiment_type=(
                        "PORTFOLIO_EXPERIMENT"
                    ),
                    natural_key=natural_key,
                )
            )

            status = normalize_status(
                first_value(
                    data,
                    "decision",
                    "promotion_decision",
                    "status",
                    default="COMPLETED",
                )
            )

            add_record(
                experiment_id=experiment_id,
                experiment_type=(
                    "PORTFOLIO_EXPERIMENT"
                ),
                natural_key=natural_key,
                title=text(
                    first_value(
                        data,
                        "name",
                        "portfolio_name",
                        default=natural_key,
                    )
                ),
                description=text(
                    first_value(
                        data,
                        "reason",
                        "rationale",
                    )
                ),
                parent_engine_id="",
                engine_family="portfolio",
                hypothesis_id="",
                variant_id="",
                portfolio_experiment_id=(
                    natural_key
                ),
                status=status,
                now=now,
                state_hash=state_hash,
                source_name=source_name,
                source_record_key=natural_key,
                raw_payload=data,
                experiments=experiments,
                observations=observations,
                metrics=metrics,
                artifacts=artifacts,
                statuses=statuses,
            )


def process_orchestrator_runs(
    *,
    frame: pd.DataFrame,
    report: dict,
    now: str,
    state_hash: str,
    experiments: list,
    observations: list,
    metrics: list,
    artifacts: list,
    statuses: list,
    orchestrator_runs: list,
) -> None:
    records = []

    if frame is not None and not frame.empty:
        records.extend(
            frame.to_dict(
                orient="records"
            )
        )

    if report:
        records.append(report)

    for index, data in enumerate(records):
        run_id = text(
            first_value(
                data,
                "run_id",
                default=f"ORCH-RUN-{index}",
            )
        )

        experiment_id = (
            build_experiment_id(
                experiment_type=(
                    "RESEARCH_CYCLE"
                ),
                natural_key=run_id,
            )
        )

        status = (
            "COMPLETED"
            if bool(
                data.get(
                    "success",
                    False,
                )
            )
            else "FAILED"
        )

        add_record(
            experiment_id=experiment_id,
            experiment_type=(
                "RESEARCH_CYCLE"
            ),
            natural_key=run_id,
            title=(
                f"Research cycle {run_id}"
            ),
            description=text(
                data.get(
                    "summary",
                    "",
                )
            ),
            parent_engine_id="",
            engine_family="orchestration",
            hypothesis_id="",
            variant_id="",
            portfolio_experiment_id="",
            status=status,
            now=now,
            state_hash=text(
                first_value(
                    data,
                    "initial_state_hash",
                    "state_hash",
                    default=state_hash,
                )
            ),
            source_name=(
                "research_orchestrator"
            ),
            source_record_key=run_id,
            raw_payload=data,
            experiments=experiments,
            observations=observations,
            metrics=metrics,
            artifacts=artifacts,
            statuses=statuses,
        )

        orchestrator_runs.append({
            "run_id": run_id,
            "experiment_id": (
                experiment_id
            ),
            "mode": text(
                data.get("mode")
            ),
            "started_at": text(
                data.get("started_at")
            ),
            "completed_at": text(
                data.get("completed_at")
            ),
            "state_hash": text(
                first_value(
                    data,
                    "initial_state_hash",
                    "state_hash",
                )
            ),
            "planned_jobs": integer(
                first_value(
                    data,
                    "planned_jobs",
                    default=(
                        data.get(
                            "counts",
                            {},
                        ).get(
                            "planned_jobs",
                            0,
                        )
                        if isinstance(
                            data.get(
                                "counts"
                            ),
                            dict,
                        )
                        else 0
                    ),
                )
            ),
            "successful_jobs": integer(
                first_value(
                    data,
                    "successful_jobs",
                    default=(
                        data.get(
                            "counts",
                            {},
                        ).get(
                            "successful_jobs",
                            0,
                        )
                        if isinstance(
                            data.get(
                                "counts"
                            ),
                            dict,
                        )
                        else 0
                    ),
                )
            ),
            "failed_jobs": integer(
                first_value(
                    data,
                    "failed_jobs",
                    default=(
                        data.get(
                            "counts",
                            {},
                        ).get(
                            "failed_jobs",
                            0,
                        )
                        if isinstance(
                            data.get(
                                "counts"
                            ),
                            dict,
                        )
                        else 0
                    ),
                )
            ),
            "success": bool(
                data.get(
                    "success",
                    False,
                )
            ),
            "execution_instruction": False,
        })


def add_record(
    *,
    experiment_id: str,
    experiment_type: str,
    natural_key: str,
    title: str,
    description: str,
    parent_engine_id: str,
    engine_family: str,
    hypothesis_id: str,
    variant_id: str,
    portfolio_experiment_id: str,
    status: str,
    now: str,
    state_hash: str,
    source_name: str,
    source_record_key: str,
    raw_payload: dict,
    experiments: list,
    observations: list,
    metrics: list,
    artifacts: list,
    statuses: list,
) -> None:
    evidence_hash = hash_payload(
        raw_payload
    )

    observation_id = (
        build_observation_id(
            experiment_id=experiment_id,
            source=source_name,
            evidence_hash=evidence_hash,
        )
    )

    experiments.append({
        "experiment_id": experiment_id,
        "experiment_type": (
            experiment_type
        ),
        "natural_key": natural_key,
        "title": title,
        "description": description,
        "parent_engine_id": (
            parent_engine_id
        ),
        "engine_family": engine_family,
        "hypothesis_id": hypothesis_id,
        "variant_id": variant_id,
        "portfolio_experiment_id": (
            portfolio_experiment_id
        ),
        "current_status": status,
        "created_at": now,
        "first_observed_at": now,
        "last_observed_at": now,
        "latest_state_hash": (
            state_hash
        ),
        "latest_source": source_name,
        "manual_decision": text(
            first_value(
                raw_payload,
                "manual_decision",
                "decision",
            )
        ),
        "reviewer": text(
            first_value(
                raw_payload,
                "manual_reviewer",
                "reviewer",
            )
        ),
        "production_eligible": False,
        "execution_instruction": False,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "source": SOURCE,
    })

    observations.append({
        "observation_id": (
            observation_id
        ),
        "experiment_id": experiment_id,
        "observed_at": now,
        "source_name": source_name,
        "source_record_key": (
            source_record_key
        ),
        "state_hash": state_hash,
        "evidence_hash": (
            evidence_hash
        ),
        "status": status,
        "decision": text(
            first_value(
                raw_payload,
                "manual_decision",
                "decision",
                "recommended_decision",
            )
        ),
        "summary": text(
            first_value(
                raw_payload,
                "summary",
                "rationale",
                "reason",
                "description",
            )
        ),
        "payload_json": (
            json_string(raw_payload)
        ),
        "execution_instruction": False,
    })

    statuses.append({
        "status_record_id": (
            f"STATUS-{observation_id}"
        ),
        "experiment_id": (
            experiment_id
        ),
        "observation_id": (
            observation_id
        ),
        "status": status,
        "recorded_at": now,
        "source_name": source_name,
        "execution_instruction": False,
    })

    artifacts.append({
        "artifact_record_id": (
            f"ART-{observation_id}"
        ),
        "experiment_id": (
            experiment_id
        ),
        "observation_id": (
            observation_id
        ),
        "artifact_type": (
            "SOURCE_RECORD"
        ),
        "artifact_path": source_name,
        "artifact_hash": evidence_hash,
        "state_hash": state_hash,
        "execution_instruction": False,
    })

    for key, value in (
        raw_payload.items()
    ):
        if isinstance(
            value,
            bool,
        ):
            continue

        if isinstance(
            value,
            (int, float),
        ):
            metrics.append({
                "metric_record_id": (
                    f"MET-{observation_id}-{key}"
                ),
                "observation_id": (
                    observation_id
                ),
                "experiment_id": (
                    experiment_id
                ),
                "metric_name": str(key),
                "metric_value": number(
                    value
                ),
                "metric_text": "",
                "metric_unit": "",
                "source_name": (
                    source_name
                ),
            })


def add_relationship(
    *,
    relationships: list,
    from_experiment_id: str,
    relationship_type: str,
    to_experiment_id: str,
    source_name: str,
    payload: dict,
) -> None:
    evidence_hash = hash_payload(
        payload
    )

    relationship_id = (
        "REL-"
        + hash_payload({
            "from": from_experiment_id,
            "type": relationship_type,
            "to": to_experiment_id,
        })[:20]
    )

    relationships.append({
        "relationship_id": (
            relationship_id
        ),
        "from_experiment_id": (
            from_experiment_id
        ),
        "relationship_type": (
            relationship_type
        ),
        "to_experiment_id": (
            to_experiment_id
        ),
        "source_name": source_name,
        "evidence_hash": evidence_hash,
    })


def validation_passed(
    data: dict,
) -> bool:
    for key in (
        "validation_passed",
        "passed",
        "success",
        "eligible",
    ):
        if key in data:
            return bool(data.get(key))

    decision = text(
        first_value(
            data,
            "decision",
            "validation_decision",
        )
    ).upper()

    return decision in {
        "VALIDATED",
        "PROMOTE",
        "APPROVE",
        "APPROVED",
        "PASS",
    }


def infer_variant_status(
    source_name: str,
    data: dict,
) -> str:
    if source_name == "validated_variants":
        return "VALIDATED"

    if source_name == "variant_review":
        return normalize_status(
            first_value(
                data,
                "recommended_decision",
                "decision",
                default="VALIDATED",
            )
        )

    if source_name == "variant_decisions":
        return normalize_status(
            first_value(
                data,
                "manual_decision",
                default="VALIDATED",
            )
        )

    if source_name == "implementation_plans":
        return normalize_status(
            first_value(
                data,
                "plan_status",
                "implementation_status",
                default="PLANNED",
            )
        )

    return "VALIDATED"


def normalize_status(
    value: Any,
) -> str:
    normalized = text(
        value
    ).strip().upper()

    aliases = {
        "PROMOTE": "VALIDATED",
        "APPROVE": "APPROVED",
        "HOLD": "DEFERRED",
        "REVISE": "VALIDATING",
        "RETIRE": "ARCHIVED",
        "PENDING": "PROPOSED",
        "PASS": "VALIDATED",
        "FAIL": "REJECTED",
        "NOT_IMPLEMENTED": "PLANNED",
    }

    return aliases.get(
        normalized,
        normalized or "PROPOSED",
    )


def frame_from_rows(
    rows: list[dict],
    columns: list[str],
) -> pd.DataFrame:
    frame = pd.DataFrame(rows)

    for column in columns:
        if column not in frame.columns:
            frame[column] = ""

    return frame[columns]


def json_string(
    payload: dict,
) -> str:
    import json

    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )
