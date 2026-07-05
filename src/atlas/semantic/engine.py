"""Semantic executive synthesis engine."""

from __future__ import annotations

from typing import Any

from atlas.semantic.career import build_career_summary
from atlas.semantic.emotion import build_emotion_summary
from atlas.semantic.growth import build_growth_summary
from atlas.semantic.identity import build_identity_summary
from atlas.semantic.mind import build_mind_summary
from atlas.semantic.motivation import build_motivation_summary
from atlas.semantic.relationships import build_relationship_summary
from atlas.semantic.stress import build_stress_summary
from atlas.semantic.common import confidence


DOMAIN_BUILDERS = [
    build_identity_summary,
    build_mind_summary,
    build_motivation_summary,
    build_emotion_summary,
    build_relationship_summary,
    build_career_summary,
    build_stress_summary,
    build_growth_summary,
]


def build_semantic_profile(payload: dict[str, Any]) -> dict[str, Any]:
    """Build semantic intelligence summary from canonical profile payload."""
    domains = [builder(payload) for builder in DOMAIN_BUILDERS]

    executive_summary = build_executive_summary(payload, domains)

    return {
        "success": True,
        "version": "1.0",
        "profile_key": payload.get("profile_key"),
        "kind": "semantic_profile",
        "executive_summary": executive_summary,
        "domains": domains,
        "confidence": aggregate_confidence(domains),
        "evidence": collect_evidence(domains),
    }


def build_executive_summary(
    payload: dict[str, Any],
    domains: list[dict[str, Any]],
) -> str:
    """Build executive semantic summary."""
    identity = payload.get("identity", {})
    classification = payload.get("classification", {})
    topology = payload.get("topology", {})
    resonance = payload.get("resonance", {})

    name = identity.get("display_name") or identity.get("name") or payload.get("profile_key", "This profile")
    role = classification.get("structural_role", "Unresolved Structural Actor")
    function = classification.get("civilization_function", "")
    topology_class = topology.get("topology_class", "unresolved topology")
    resonance_class = resonance.get("resonance_class", "unresolved resonance")

    parts = [
        f"{name} is compiled by Atlas as a **{role}**.",
    ]

    if function:
        parts.append(function)

    parts.append(
        f"The profile's structural organization currently resolves as **{topology_class}**, "
        f"with a **{resonance_class}** resonance pattern."
    )

    mind = find_domain(domains, "mind")
    if mind:
        parts.append(mind.get("summary", ""))

    growth = find_domain(domains, "growth")
    if growth:
        parts.append(growth.get("summary", ""))

    return "\n\n".join(part for part in parts if part)


def find_domain(domains: list[dict[str, Any]], name: str) -> dict[str, Any]:
    """Find domain by name."""
    for domain in domains:
        if domain.get("domain") == name:
            return domain
    return {}


def aggregate_confidence(domains: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate domain confidence."""
    scores = [
        domain.get("confidence", {}).get("score")
        for domain in domains
        if isinstance(domain.get("confidence"), dict)
    ]
    scores = [score for score in scores if isinstance(score, (int, float))]

    if not scores:
        return confidence(0.0)

    return confidence(sum(scores) / len(scores))


def collect_evidence(domains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collect evidence from semantic domains."""
    evidence: list[dict[str, Any]] = []
    for domain in domains:
        items = domain.get("evidence", [])
        if isinstance(items, list):
            evidence.extend(items)
    return evidence
