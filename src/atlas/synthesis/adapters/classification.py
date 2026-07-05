
"""Classification evidence adapter."""

from __future__ import annotations

from typing import Any

from atlas.synthesis.evidence import StructuralEvidence, make_evidence
from atlas.synthesis.adapters.utils import make_record, safe_dict, safe_float


def collect(payload: dict[str, Any]) -> list[StructuralEvidence]:
    """Collect evidence from Structural Classification."""
    classification = safe_dict(payload.get("classification"))

    role = classification.get("structural_role")
    subtype = classification.get("structural_subtype")
    confidence = safe_dict(classification.get("confidence"))
    score = safe_float(confidence.get("score"), 0.75)

    evidence: list[StructuralEvidence] = []

    if role == "Persistence-Architect":
        evidence.append(make_record("classification.role", "persistent_architecture", role, score))
    elif role == "Cycle-Weaver":
        evidence.append(make_record("classification.role", "recursive_patterning", role, score))
    elif role == "Connector-Architect":
        evidence.append(make_record("classification.role", "distributed_integration", role, score))
    elif role == "Pattern-Weaver":
        evidence.append(make_record("classification.role", "information_routing", role, score))
        evidence.append(make_record("classification.role", "high_truth_density", role, min(1.0, score + 0.05)))
    elif role == "Amplifier-Connector":
        evidence.append(make_record("classification.role", "visible_authorship", role, score))

    if subtype and subtype != "Unresolved Subtype":
        evidence.append(
            make_evidence(
                engine="classification.subtype",
                feature="structural_subtype",
                category="identity_architecture",
                value=subtype,
                confidence=score,
                weight=0.75,
                explanation=f"Structural subtype resolves as {subtype}.",
                source="classification",
                tags=["classification", "subtype"],
            )
        )

    return evidence
