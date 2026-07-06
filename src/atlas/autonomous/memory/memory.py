
"""Autonomous Research Memory."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


MEMORY_VERSION = "1.0.0"


def create_research_memory() -> dict[str, Any]:
    """Create empty research memory."""
    return {
        "success": True,
        "version": MEMORY_VERSION,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "experiments": {},
        "evidence": {},
        "hypotheses": {},
        "notes": [],
    }


def remember_experiment(memory: dict[str, Any], experiment: dict[str, Any]) -> dict[str, Any]:
    """Store experiment result."""
    experiment_id = str(experiment.get("experiment_id") or experiment.get("task_id") or "experiment::unknown")

    existing = memory.setdefault("experiments", {}).get(experiment_id, {})

    memory["experiments"][experiment_id] = {
        **existing,
        **experiment,
        "experiment_id": experiment_id,
        "created_at": existing.get("created_at") or utc_now(),
        "updated_at": utc_now(),
    }
    memory["updated_at"] = utc_now()
    return memory


def remember_evidence(memory: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    """Store evidence result."""
    evidence_id = str(evidence.get("evidence_id") or "evidence::unknown")

    existing = memory.setdefault("evidence", {}).get(evidence_id, {})

    memory["evidence"][evidence_id] = {
        **existing,
        **evidence,
        "evidence_id": evidence_id,
        "created_at": existing.get("created_at") or utc_now(),
        "updated_at": utc_now(),
    }
    memory["updated_at"] = utc_now()
    return memory


def remember_hypothesis(memory: dict[str, Any], hypothesis: dict[str, Any]) -> dict[str, Any]:
    """Store hypothesis result."""
    hypothesis_id = str(hypothesis.get("hypothesis_id") or hypothesis.get("candidate_id") or "hypothesis::unknown")

    existing = memory.setdefault("hypotheses", {}).get(hypothesis_id, {})

    memory["hypotheses"][hypothesis_id] = {
        **existing,
        **hypothesis,
        "hypothesis_id": hypothesis_id,
        "created_at": existing.get("created_at") or utc_now(),
        "updated_at": utc_now(),
    }
    memory["updated_at"] = utc_now()
    return memory


def add_memory_note(memory: dict[str, Any], note: str, *, source: str = "system") -> dict[str, Any]:
    """Add memory note."""
    memory.setdefault("notes", []).append(
        {
            "source": source,
            "note": note,
            "created_at": utc_now(),
        }
    )
    memory["updated_at"] = utc_now()
    return memory


def utc_now() -> str:
    """Return UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()
