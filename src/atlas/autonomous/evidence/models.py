
"""Autonomous Evidence models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


EVIDENCE_MODEL_VERSION = "1.0.0"


@dataclass(frozen=True)
class EvidenceRecord:
    """Standardized scientific evidence object."""

    evidence_id: str
    source_engine: str
    question: str
    observation: str
    variables: list[str]
    sample_size: int
    confidence: float
    effect_size: float
    status: str = "active"
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def evidence_to_dict(record: EvidenceRecord) -> dict[str, Any]:
    """Convert EvidenceRecord to dict."""
    return asdict(record)
