
"""Service layer for Knowledge Lab."""

from __future__ import annotations

from typing import Any

from atlas.compiler.canonical_profile_compiler import compile_canonical_profile
from atlas.knowledge import build_knowledge_graph_from_discovery, build_knowledge_interpretation
from atlas.library.profile_library import list_saved_profiles
from atlas.services.discovery_service import build_discovery_payload


def list_knowledge_profiles() -> list[str]:
    """List saved profiles."""
    return list_saved_profiles()


def build_knowledge_lab_payload(
    profile_key: str,
    *,
    discovery_limit: int = 25,
    force: bool = False,
) -> dict[str, Any]:
    """Build Knowledge Lab payload."""
    payload = compile_canonical_profile(profile_key, force=force)

    if not payload.get("success"):
        return {
            "success": False,
            "profile_key": profile_key,
            "errors": payload.get("errors", []),
        }

    interpretation = payload.get("knowledge_interpretation") or build_knowledge_interpretation(payload)

    discovery_payload = build_discovery_payload(
        limit=discovery_limit,
        force=False,
    )
    knowledge_graph = build_knowledge_graph_from_discovery(
        discovery_payload.get("discovery", {})
    )

    return {
        "success": True,
        "profile_key": profile_key,
        "payload": payload,
        "knowledge_interpretation": interpretation,
        "knowledge_graph": knowledge_graph,
        "discovery_summary": discovery_payload.get("summary", ""),
    }
