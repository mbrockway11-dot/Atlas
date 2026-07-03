"""Atlas AI orchestration layer.

Coordinates the research AI services through their real public contracts.

Atlas has two distinct intelligence modes:

1. Profile intelligence
   - compiler / temporal / graph / IVE / population
   - starts from a profile/canonical payload

2. Research intelligence
   - reasoning / hypothesis / falsification / experiment / discovery / memory
   - starts from a natural-language query

This module focuses on the research intelligence pipeline.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from typing import Any

from atlas.services.discovery_engine_service import build_discovery_payload
from atlas.services.experiment_planner_service import build_experiment_plan_payload
from atlas.services.falsification_engine_service import build_falsification_payload
from atlas.services.hypothesis_engine_service import build_hypothesis_payload
from atlas.services.query_planner_service import build_query_plan_payload
from atlas.services.research_memory_service import build_research_memory_payload


AI_ORCHESTRATOR_VERSION = "3.0"


@dataclass(slots=True)
class AIStageResult:
    """Result from one AI runtime stage."""

    name: str
    status: str
    payload: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AIRuntimePayload:
    """Unified AI runtime payload."""

    success: bool
    version: str
    timestamp: str
    query: str
    subject: str | None
    mode: str
    stages: dict[str, AIStageResult]
    integrated: dict[str, Any]
    warnings: list[str]
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe dictionary payload."""
        return {
            "success": self.success,
            "version": self.version,
            "timestamp": self.timestamp,
            "query": self.query,
            "subject": self.subject,
            "mode": self.mode,
            "stages": {
                name: normalize_payload(result)
                for name, result in self.stages.items()
            },
            "integrated": self.integrated,
            "warnings": self.warnings,
            "errors": self.errors,
        }


def run_research_pipeline(
    query: str,
    *,
    subject: str | None = None,
    include_discovery: bool = True,
    discovery_limit: int = 10,
) -> AIRuntimePayload:
    """Run the Atlas research AI pipeline from a natural-language query."""
    clean_query = query.strip()

    if not clean_query:
        return AIRuntimePayload(
            success=False,
            version=AI_ORCHESTRATOR_VERSION,
            timestamp=datetime.now(UTC).isoformat(),
            query=query,
            subject=subject,
            mode="research",
            stages={},
            integrated={},
            warnings=[],
            errors=["Query is required."],
        )

    stages: dict[str, AIStageResult] = {}

    stages["query_planner"] = run_stage(
        "query_planner",
        lambda: build_query_plan_payload(clean_query),
    )

    stages["hypothesis"] = run_stage(
        "hypothesis",
        lambda: build_hypothesis_payload(clean_query),
    )

    stages["falsification"] = run_stage(
        "falsification",
        lambda: build_falsification_payload(clean_query),
    )

    stages["experiment_planner"] = run_stage(
        "experiment_planner",
        lambda: build_experiment_plan_payload(clean_query),
    )

    if include_discovery:
        stages["discovery"] = run_stage(
            "discovery",
            lambda: build_discovery_payload(limit=discovery_limit),
        )

    stages["research_memory"] = run_stage(
        "research_memory",
        lambda: build_research_memory_payload(
            clean_query,
            include_discovery=include_discovery,
            discovery_limit=discovery_limit,
        ),
    )

    warnings = collect_stage_messages(stages, "warnings")
    errors = collect_stage_messages(stages, "errors")

    integrated = integrate_research_results(
        query=clean_query,
        subject=subject,
        stages=stages,
    )

    return AIRuntimePayload(
        success=not errors,
        version=AI_ORCHESTRATOR_VERSION,
        timestamp=datetime.now(UTC).isoformat(),
        query=clean_query,
        subject=subject,
        mode="research",
        stages=stages,
        integrated=integrated,
        warnings=warnings,
        errors=errors,
    )


def run_ai_pipeline(
    *,
    query: str | None = None,
    subject: str | None = None,
    compiler_payload: dict[str, Any] | None = None,
    profile_payload: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> AIRuntimePayload:
    """Compatibility entry point.

    If query is supplied, run the research AI pipeline.

    If only subject/profile context is supplied, synthesize a research query.
    This keeps old smoke tests working while honoring the actual service API.
    """
    if query:
        return run_research_pipeline(query, subject=subject)

    inferred_subject = (
        subject
        or extract_subject(compiler_payload or {})
        or extract_subject(profile_payload or {})
        or (context or {}).get("subject")
        or "Atlas profile"
    )

    synthesized_query = f"Analyze the strongest research hypotheses for {inferred_subject}."

    return run_research_pipeline(
        synthesized_query,
        subject=inferred_subject,
    )


def run_stage(name: str, fn) -> AIStageResult:
    """Run one stage and normalize its payload."""
    try:
        raw = fn()
    except Exception as exc:
        return AIStageResult(
            name=name,
            status="error",
            payload={},
            errors=[f"{name}: {exc}"],
        )

    payload = normalize_payload(raw)
    warnings = collect_messages(payload, "warnings")
    errors = collect_messages(payload, "errors")

    status = str(payload.get("status") or ("error" if errors else "ok"))

    return AIStageResult(
        name=name,
        status=status,
        payload=payload,
        warnings=warnings,
        errors=errors,
    )


def integrate_research_results(
    *,
    query: str,
    subject: str | None,
    stages: dict[str, AIStageResult],
) -> dict[str, Any]:
    """Build unified research AI summary."""
    completed = [
        name for name, result in stages.items()
        if result.status != "error"
    ]

    failed = [
        name for name, result in stages.items()
        if result.status == "error"
    ]

    hypotheses = extract_first_list(
        stages.get("hypothesis"),
        keys=("hypotheses", "items", "results"),
    )

    falsifications = extract_first_list(
        stages.get("falsification"),
        keys=("cases", "falsification_cases", "tests", "items", "results"),
    )

    experiments = extract_first_list(
        stages.get("experiment_planner"),
        keys=("experiments", "plans", "items", "results"),
    )

    discoveries = extract_first_list(
        stages.get("discovery"),
        keys=("discoveries", "signals", "items", "results"),
    )

    return {
        "query": query,
        "subject": subject,
        "runtime_status": "ok" if not failed else "partial",
        "completed_stages": completed,
        "failed_stages": failed,
        "hypothesis_count": len(hypotheses),
        "falsification_count": len(falsifications),
        "experiment_count": len(experiments),
        "discovery_count": len(discoveries),
        "has_research_memory": bool(stages.get("research_memory")),
        "summary": [
            f"Completed AI stages: {len(completed)}",
            f"Available hypotheses: {len(hypotheses)}",
            f"Available falsification checks: {len(falsifications)}",
            f"Available experiment plans: {len(experiments)}",
            f"Available discovery signals: {len(discoveries)}",
            (
                "AI research runtime completed successfully."
                if not failed
                else f"Failed stages: {', '.join(failed)}"
            ),
        ],
    }


def normalize_payload(value: Any) -> dict[str, Any]:
    """Normalize arbitrary service output into a dictionary."""
    if value is None:
        return {}

    if isinstance(value, dict):
        return value

    if is_dataclass(value):
        return asdict(value)

    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        result = to_dict()
        return result if isinstance(result, dict) else {"value": result}

    if isinstance(value, list):
        return {"items": value}

    if isinstance(value, tuple):
        return {"items": list(value)}

    return {"value": value}


def collect_messages(payload: dict[str, Any], key: str) -> list[str]:
    """Collect warning/error messages from a payload."""
    value = payload.get(key)

    if value is None:
        return []

    if isinstance(value, list):
        return [str(item) for item in value]

    return [str(value)]


def collect_stage_messages(
    stages: dict[str, AIStageResult],
    key: str,
) -> list[str]:
    """Collect warning/error messages across stages."""
    messages: list[str] = []

    for stage in stages.values():
        values = getattr(stage, key)
        messages.extend(str(value) for value in values)

    return messages


def extract_first_list(
    stage: AIStageResult | None,
    *,
    keys: tuple[str, ...],
) -> list[Any]:
    """Extract the first list-like value from a stage payload."""
    if stage is None or not stage.payload:
        return []

    for key in keys:
        value = stage.payload.get(key)

        if value is None and isinstance(stage.payload.get("data"), dict):
            value = stage.payload["data"].get(key)

        if isinstance(value, list):
            return value

        if value is not None:
            return [value]

    return []


def extract_subject(payload: dict[str, Any]) -> str | None:
    """Best-effort subject extraction from compiler/profile payloads."""
    if not payload:
        return None

    direct = payload.get("name") or payload.get("profile_name") or payload.get("subject")
    if direct:
        return str(direct)

    data = payload.get("data")
    if isinstance(data, dict):
        identity = data.get("identity")
        if isinstance(identity, dict) and identity.get("name"):
            return str(identity["name"])

    identity = payload.get("identity")
    if isinstance(identity, dict) and identity.get("name"):
        return str(identity["name"])

    return None


