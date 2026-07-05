"""Semantic identity domain."""

from __future__ import annotations

from typing import Any

from atlas.semantic.common import confidence, evidence_item, sentence_join


def build_identity_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build semantic identity summary."""
    identity = payload.get("identity", {})
    birth = payload.get("birth", {})
    lifecycle = payload.get("lifecycle", {})

    name = identity.get("display_name") or identity.get("name") or payload.get("profile_key", "This profile")
    role = payload.get("classification", {}).get("structural_role", "an unresolved structural role")

    summary = sentence_join([
        f"{name} is compiled by Atlas as {role}.",
        "The identity layer anchors the dossier by normalizing name, profile key, birth metadata, and lifecycle state before higher-order interpretation is produced.",
        "This layer should be read as the factual foundation of the profile rather than an interpretive claim.",
    ])

    return {
        "domain": "identity",
        "title": "Identity Architecture",
        "summary": summary,
        "confidence": confidence(0.9 if identity else 0.35),
        "evidence": [
            evidence_item("identity", "Identity metadata is available.", identity),
            evidence_item("birth", "Birth metadata contributes to temporal compilation.", birth),
            evidence_item("lifecycle", "Lifecycle metadata contributes contextual state.", lifecycle),
        ],
    }
