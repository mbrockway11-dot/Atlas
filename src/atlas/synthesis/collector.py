
"""Evidence collector for Atlas Synthesis."""

from __future__ import annotations

from atlas.synthesis.adapters import (
    gematria,
    behavior,
    classification,
    graph,
    population,
    resonance,
    topology,
)
from atlas.synthesis.evidence import (
    EvidenceBundle,
    StructuralEvidence,
    make_evidence,
)


SYNTHESIS_COLLECTOR_VERSION = "1.0"


def collect_structural_evidence(profile_key: str) -> EvidenceBundle:
    """Collect standardized StructuralEvidence for one compiled profile."""
    from atlas.compiler.canonical_profile_compiler import compile_canonical_profile

    payload = compile_canonical_profile(profile_key, force=False)
    return collect_structural_evidence_from_payload(profile_key, payload)


def collect_structural_evidence_from_payload(
    profile_key: str,
    payload: dict,
) -> EvidenceBundle:
    """Collect standardized StructuralEvidence from an existing payload."""
    evidence: list[StructuralEvidence] = []

    if not payload.get("success"):
        evidence.append(
            make_evidence(
                engine="compiler",
                feature="compile_failure",
                category="structural_risk",
                value=True,
                confidence=1.0,
                weight=1.0,
                explanation="Canonical profile compilation failed.",
                source="compile_canonical_profile",
                tags=["compiler", "error"],
            )
        )

        return EvidenceBundle(
            version=SYNTHESIS_COLLECTOR_VERSION,
            profile_key=profile_key,
            evidence=tuple(evidence),
        )

    evidence.extend(graph.collect(payload))
    evidence.extend(classification.collect(payload))
    evidence.extend(topology.collect(payload))
    evidence.extend(resonance.collect(payload))
    evidence.extend(population.collect(payload))
    evidence.extend(behavior.collect(payload))
    evidence.extend(gematria.collect(payload))

    return EvidenceBundle(
        version=SYNTHESIS_COLLECTOR_VERSION,
        profile_key=profile_key,
        evidence=tuple(evidence),
    )
