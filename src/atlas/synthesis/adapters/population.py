
"""Population proxy evidence adapter."""

from __future__ import annotations

from typing import Any

from atlas.synthesis.evidence import StructuralEvidence
from atlas.synthesis.adapters.utils import make_record, safe_dict, safe_float


def collect(payload: dict[str, Any]) -> list[StructuralEvidence]:
    """Collect lightweight population evidence already embedded in payload."""
    classification = safe_dict(payload.get("classification"))
    basis = safe_dict(classification.get("basis"))

    evidence: list[StructuralEvidence] = []

    motif_richness = safe_float(basis.get("motif_richness"))
    raw_edges = safe_float(basis.get("raw_edge_count"))
    truth_edges = safe_float(basis.get("truth_edge_count"))

    if motif_richness >= 0.80:
        evidence.append(make_record("population.proxy", "rare_signature", "high motif richness", 0.72))

    if raw_edges >= 300:
        evidence.append(make_record("population.proxy", "high_impact_signature", "high raw edge count", 0.74))

    if truth_edges >= 40:
        evidence.append(make_record("population.proxy", "high_impact_signature", "high truth edge count", 0.78))

    return evidence
