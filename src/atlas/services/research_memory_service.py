"""Atlas Research Memory service.

Persistent research memory for Atlas cognitive outputs.

Purpose:
- Store reasoning, hypothesis, falsification, experiment, and discovery runs.
- Reuse prior research.
- Track confidence, subjects, queries, conclusions, and recommended actions.
- Provide a foundation for future knowledge-graph construction.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from atlas.services.discovery_engine_service import build_discovery_payload
from atlas.services.experiment_planner_service import build_experiment_plan_payload
from atlas.services.falsification_engine_service import build_falsification_payload
from atlas.services.hypothesis_engine_service import build_hypothesis_payload
from atlas.services.reasoning_service import build_reasoning_payload


RESEARCH_MEMORY_VERSION = "1.0"

MEMORY_ROOT = Path("output") / "research_memory"
MEMORY_INDEX_PATH = MEMORY_ROOT / "research_memory_index.json"


def build_research_memory_payload(
    query: str,
    *,
    include_discovery: bool = False,
    discovery_limit: int = 10,
) -> dict[str, Any]:
    """Run Atlas cognitive chain and persist a research memory record."""
    MEMORY_ROOT.mkdir(parents=True, exist_ok=True)

    reasoning_payload = safe_call("reasoning", lambda: build_reasoning_payload(query))
    hypothesis_payload = safe_call("hypothesis", lambda: build_hypothesis_payload(query))
    falsification_payload = safe_call(
        "falsification",
        lambda: build_falsification_payload(query),
    )
    experiment_payload = safe_call(
        "experiment",
        lambda: build_experiment_plan_payload(query),
    )

    discovery_payload = {}
    if include_discovery:
        discovery_payload = safe_call(
            "discovery",
            lambda: build_discovery_payload(limit=discovery_limit),
        )

    record = build_memory_record(
        query=query,
        reasoning_payload=reasoning_payload,
        hypothesis_payload=hypothesis_payload,
        falsification_payload=falsification_payload,
        experiment_payload=experiment_payload,
        discovery_payload=discovery_payload,
    )

    write_memory_record(record)
    update_memory_index(record)

    return {
        "success": True,
        "version": RESEARCH_MEMORY_VERSION,
        "query": query,
        "errors": collect_record_errors(record),
        "warnings": collect_record_warnings(record),
        "data": {
            "memory_record": record,
            "memory_path": str(record.get("path", "")),
            "index_path": str(MEMORY_INDEX_PATH),
        },
        "exports": {
            "memory_json": record,
            "markdown": render_memory_markdown(record),
        },
        "metrics": build_memory_metrics(record),
    }


def list_research_memory_records() -> list[dict[str, Any]]:
    """List saved research memory records."""
    index = load_memory_index()
    return index.get("records", [])


def read_research_memory_record(record_id: str) -> dict[str, Any]:
    """Read one research memory record."""
    index = load_memory_index()

    for item in index.get("records", []):
        if item.get("record_id") == record_id:
            path = Path(item.get("path", ""))
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))

    return {
        "success": False,
        "error": f"Research memory record not found: {record_id}",
    }


def search_research_memory(
    query: str,
    *,
    limit: int = 20,
) -> dict[str, Any]:
    """Search research memory index by query text."""
    normalized = normalize_text(query)
    index = load_memory_index()

    matches = []

    for item in index.get("records", []):
        haystack = normalize_text(
            " ".join(
                [
                    item.get("query", ""),
                    item.get("subject", ""),
                    item.get("scope", ""),
                    item.get("intent", ""),
                    item.get("best_hypothesis", ""),
                    item.get("recommended_experiment", ""),
                ]
            )
        )

        if normalized in haystack or any(token in haystack for token in normalized.split()):
            matches.append(item)

    return {
        "success": True,
        "version": RESEARCH_MEMORY_VERSION,
        "query": query,
        "matches": matches[:limit],
        "match_count": len(matches),
    }


def build_memory_record(
    *,
    query: str,
    reasoning_payload: dict[str, Any],
    hypothesis_payload: dict[str, Any],
    falsification_payload: dict[str, Any],
    experiment_payload: dict[str, Any],
    discovery_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build one memory record."""
    timestamp = now_iso()
    record_id = build_record_id(query, timestamp)

    reasoning = reasoning_payload.get("data", {}).get("reasoning", {})
    hypothesis_model = hypothesis_payload.get("data", {}).get("hypothesis_model", {})
    falsification_model = falsification_payload.get("data", {}).get("falsification_model", {})
    experiment_model = experiment_payload.get("data", {}).get("experiment_model", {})
    discovery_model = discovery_payload.get("data", {}).get("discovery_model", {})

    record = {
        "success": True,
        "version": RESEARCH_MEMORY_VERSION,
        "record_id": record_id,
        "timestamp": timestamp,
        "query": query,
        "subject": reasoning.get("subject", hypothesis_model.get("subject", "unknown")),
        "intent": reasoning.get("intent", hypothesis_model.get("intent", "unknown")),
        "scope": reasoning.get("scope", hypothesis_model.get("scope", "unknown")),
        "confidence": {
            "reasoning": reasoning.get("confidence", {}).get("overall", {}),
            "best_hypothesis": hypothesis_model.get("best_supported_hypothesis", {}).get(
                "confidence",
                {},
            ),
            "highest_falsification_pressure": falsification_model.get(
                "highest_priority_case",
                {},
            ).get("falsification_pressure", {}),
            "experiment_value": experiment_model.get(
                "recommended_next_experiment",
                {},
            ).get("value_score", {}),
        },
        "summary": {
            "final_answer": reasoning.get("final_answer", ""),
            "best_hypothesis": hypothesis_model.get("best_supported_hypothesis", {}).get(
                "title",
                "",
            ),
            "highest_falsification_case": falsification_model.get(
                "highest_priority_case",
                {},
            ).get("hypothesis_title", ""),
            "recommended_experiment": experiment_model.get(
                "recommended_next_experiment",
                {},
            ).get("title", ""),
            "discovery_highest_priority": discovery_model.get("summary", {}).get(
                "highest_priority",
                {},
            ),
        },
        "outputs": {
            "reasoning": compact_payload(reasoning_payload),
            "hypothesis": compact_payload(hypothesis_payload),
            "falsification": compact_payload(falsification_payload),
            "experiment": compact_payload(experiment_payload),
            "discovery": compact_payload(discovery_payload) if discovery_payload else {},
        },
        "paths": {},
    }

    record["path"] = str(record_path(record_id))
    return record


def write_memory_record(record: dict[str, Any]) -> None:
    """Write memory record to disk."""
    path = record_path(record.get("record_id", "unknown"))
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")


def update_memory_index(record: dict[str, Any]) -> None:
    """Update memory index."""
    index = load_memory_index()

    item = {
        "record_id": record.get("record_id"),
        "timestamp": record.get("timestamp"),
        "query": record.get("query"),
        "subject": record.get("subject"),
        "intent": record.get("intent"),
        "scope": record.get("scope"),
        "reasoning_confidence": record.get("confidence", {}).get("reasoning", {}),
        "best_hypothesis": record.get("summary", {}).get("best_hypothesis"),
        "recommended_experiment": record.get("summary", {}).get(
            "recommended_experiment"
        ),
        "path": record.get("path"),
    }

    records = [
        existing
        for existing in index.get("records", [])
        if existing.get("record_id") != item.get("record_id")
    ]
    records.insert(0, item)

    index = {
        "version": RESEARCH_MEMORY_VERSION,
        "updated_at": now_iso(),
        "record_count": len(records),
        "records": records,
    }

    MEMORY_INDEX_PATH.write_text(
        json.dumps(index, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def load_memory_index() -> dict[str, Any]:
    """Load memory index."""
    MEMORY_ROOT.mkdir(parents=True, exist_ok=True)

    if not MEMORY_INDEX_PATH.exists():
        return {
            "version": RESEARCH_MEMORY_VERSION,
            "updated_at": now_iso(),
            "record_count": 0,
            "records": [],
        }

    try:
        return json.loads(MEMORY_INDEX_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "version": RESEARCH_MEMORY_VERSION,
            "updated_at": now_iso(),
            "record_count": 0,
            "records": [],
            "warnings": ["Memory index was unreadable and has been reset in memory."],
        }


def record_path(record_id: str) -> Path:
    """Return path for one memory record."""
    return MEMORY_ROOT / f"{record_id}.json"


def compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Create compact payload summary for memory."""
    return {
        "success": payload.get("success", False),
        "version": payload.get("version"),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "metrics": payload.get("metrics", {}),
        "data_keys": sorted(list((payload.get("data") or {}).keys())),
        "export_keys": sorted(list((payload.get("exports") or {}).keys())),
    }


def build_memory_metrics(record: dict[str, Any]) -> dict[str, Any]:
    """Build memory metrics."""
    markdown = render_memory_markdown(record)

    return {
        "record_id": record.get("record_id"),
        "subject": record.get("subject"),
        "intent": record.get("intent"),
        "scope": record.get("scope"),
        "word_count": len(markdown.split()),
        "has_reasoning": bool(record.get("outputs", {}).get("reasoning")),
        "has_hypothesis": bool(record.get("outputs", {}).get("hypothesis")),
        "has_falsification": bool(record.get("outputs", {}).get("falsification")),
        "has_experiment": bool(record.get("outputs", {}).get("experiment")),
        "has_discovery": bool(record.get("outputs", {}).get("discovery")),
        "reasoning_confidence": record.get("confidence", {}).get("reasoning", {}),
        "best_hypothesis_confidence": record.get("confidence", {}).get(
            "best_hypothesis",
            {},
        ),
    }


def render_memory_markdown(record: dict[str, Any]) -> str:
    """Render memory record as Markdown."""
    lines = [
        f"# Atlas Research Memory: {record.get('subject', 'Unknown')}",
        "",
        f"**Version:** {record.get('version', RESEARCH_MEMORY_VERSION)}",
        f"**Record ID:** {record.get('record_id')}",
        f"**Timestamp:** {record.get('timestamp')}",
        f"**Intent:** {record.get('intent')}",
        f"**Scope:** {record.get('scope')}",
        "",
        "## Query",
        record.get("query", ""),
        "",
        "## Summary",
        f"- Best hypothesis: {record.get('summary', {}).get('best_hypothesis', '')}",
        f"- Highest falsification case: {record.get('summary', {}).get('highest_falsification_case', '')}",
        f"- Recommended experiment: {record.get('summary', {}).get('recommended_experiment', '')}",
        "",
        "## Final Answer",
        record.get("summary", {}).get("final_answer", ""),
        "",
        "## Confidence",
    ]

    for key, confidence in record.get("confidence", {}).items():
        if isinstance(confidence, dict):
            lines.append(
                f"- {key}: {confidence.get('percent', 0)}% "
                f"{confidence.get('label', 'unknown')}"
            )

    return "\n".join(lines).strip() + "\n"


def safe_call(name: str, fn) -> dict[str, Any]:
    """Safely execute a service call."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "version": RESEARCH_MEMORY_VERSION,
            "errors": [f"{name} failed: {exc}"],
            "warnings": [],
            "data": {},
            "exports": {},
            "metrics": {},
        }


def collect_record_errors(record: dict[str, Any]) -> list[Any]:
    """Collect errors from compact outputs."""
    errors = []

    for name, payload in record.get("outputs", {}).items():
        for error in payload.get("errors", []):
            errors.append({"source": name, "error": error})

    return errors


def collect_record_warnings(record: dict[str, Any]) -> list[str]:
    """Collect warnings from compact outputs."""
    warnings = []

    for name, payload in record.get("outputs", {}).items():
        for warning in payload.get("warnings", []):
            text = f"{name}: {warning}"
            if text not in warnings:
                warnings.append(text)

    return warnings


def build_record_id(query: str, timestamp: str) -> str:
    """Build stable-ish memory record id."""
    raw = f"{timestamp}:{query}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:12]
    slug = slugify(query)[:60] or "atlas_research"
    return f"{timestamp_slug(timestamp)}_{slug}_{digest}"


def timestamp_slug(timestamp: str) -> str:
    """Convert timestamp to filename-safe prefix."""
    return (
        timestamp.replace(":", "")
        .replace("-", "")
        .replace(".", "")
        .replace("+", "z")
    )


def slugify(value: str) -> str:
    """Create filename-safe slug."""
    chars = []

    for char in value.lower():
        if char.isalnum():
            chars.append(char)
        elif char in {" ", "-", "_"}:
            chars.append("_")

    slug = "".join(chars)

    while "__" in slug:
        slug = slug.replace("__", "_")

    return slug.strip("_")


def normalize_text(value: str) -> str:
    """Normalize text."""
    return " ".join(value.lower().strip().split())


def now_iso() -> str:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def json_export(data: Any) -> str:
    """Serialize research memory JSON."""
    return json.dumps(data, indent=2, sort_keys=True)