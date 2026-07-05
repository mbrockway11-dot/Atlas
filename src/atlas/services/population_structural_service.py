
"""Service wrapper for structural population engines."""

from __future__ import annotations

from typing import Any

from atlas.population.structural_neighbors_v2 import find_structural_neighbors


def build_structural_neighbors_payload(
    profile_key: str,
    *,
    limit: int = 10,
    profile_keys: list[str] | None = None,
) -> dict[str, Any]:
    """Build structural neighbor payload for dashboards."""
    return find_structural_neighbors(
        profile_key,
        limit=limit,
        profile_keys=profile_keys,
    )
