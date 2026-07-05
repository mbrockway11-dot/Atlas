
"""Topology evidence adapter."""

from __future__ import annotations

from typing import Any

from atlas.synthesis.evidence import StructuralEvidence
from atlas.synthesis.adapters.utils import make_record, safe_dict, safe_float


def collect(payload: dict[str, Any]) -> list[StructuralEvidence]:
    """Collect evidence from topology vector."""
    topology = safe_dict(payload.get("topology"))
    summary = safe_dict(topology.get("summary"))
    vector = safe_dict(summary.get("topology_vector"))

    evidence: list[StructuralEvidence] = []

    if safe_float(vector.get("persistence")) >= 0.5:
        evidence.append(make_record("topology.vector", "persistent_architecture", vector.get("persistence"), 0.83))

    if safe_float(vector.get("branching")) >= 0.5:
        evidence.append(make_record("topology.vector", "distributed_integration", vector.get("branching"), 0.78))

    if safe_float(vector.get("cyclicity")) >= 0.5:
        evidence.append(make_record("topology.vector", "recursive_patterning", vector.get("cyclicity"), 0.80))

    if safe_float(vector.get("bottleneck")) >= 0.5:
        evidence.append(make_record("topology.vector", "constraint_pattern", vector.get("bottleneck"), 0.80))

    return evidence
