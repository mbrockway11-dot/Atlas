
"""Resonance evidence adapter."""

from __future__ import annotations

from typing import Any

from atlas.synthesis.evidence import StructuralEvidence
from atlas.synthesis.adapters.utils import make_record, safe_dict, safe_float


def collect(payload: dict[str, Any]) -> list[StructuralEvidence]:
    """Collect evidence from resonance vector."""
    resonance = safe_dict(payload.get("resonance"))
    summary = safe_dict(resonance.get("summary"))
    vector = safe_dict(summary.get("resonance_vector"))

    evidence: list[StructuralEvidence] = []

    if safe_float(vector.get("stability")) >= 0.5:
        evidence.append(make_record("resonance.vector", "internal_stabilization", vector.get("stability"), 0.80))

    if safe_float(vector.get("propagation")) >= 0.5:
        evidence.append(make_record("resonance.vector", "information_routing", vector.get("propagation"), 0.78))

    if safe_float(vector.get("activation")) >= 0.5:
        evidence.append(make_record("resonance.vector", "energy_allocation", vector.get("activation"), 0.75))

    if safe_float(vector.get("channeling")) >= 0.5:
        evidence.append(make_record("resonance.vector", "constraint_pattern", vector.get("channeling"), 0.76))

    return evidence
