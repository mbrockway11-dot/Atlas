
"""Autonomous Evidence Engine."""

from atlas.autonomous.evidence.builder import (
    build_evidence_from_causality,
    build_evidence_from_discovery,
)
from atlas.autonomous.evidence.confidence import aggregate_evidence_confidence
from atlas.autonomous.evidence.registry import create_evidence_registry, register_many
from atlas.autonomous.evidence.validator import validate_evidence_records

__all__ = [
    "build_evidence_from_causality",
    "build_evidence_from_discovery",
    "aggregate_evidence_confidence",
    "create_evidence_registry",
    "register_many",
    "validate_evidence_records",
]
