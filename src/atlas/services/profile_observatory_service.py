"""Profile Observatory service utilities."""

from __future__ import annotations

import json
from typing import Any

from atlas.acf.builder import export_acf_profile
from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles
from atlas.overlay import build_composite_overlay
from atlas.research import build_profile_matrix_rows
from atlas.resonance import build_resonance_field


def list_observatory_profiles() -> list[str]:
    """Return saved profile keys."""
    return list_saved_profiles()


def load_or_repair_profile_acf(profile_key: str) -> dict[str, Any] | None:
    """Load profile ACF, repairing legacy missing name fields when possible."""
    acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"

    if not acf_path.exists():
        return None

    acf = json.loads(acf_path.read_text(encoding="utf-8"))

    if acf.get("name"):
        return acf

    identity = acf.get("identity")
    if isinstance(identity, dict) and identity.get("name"):
        acf["name"] = identity["name"]
    else:
        acf["name"] = profile_key.replace("_", " ").title()

    acf_path.write_text(
        json.dumps(acf, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return acf


def build_profile_overlay(acf: dict[str, Any]) -> dict[str, Any]:
    """Build composite overlay for a profile."""
    return build_composite_overlay(acf)


def build_profile_resonance_field(acf: dict[str, Any]) -> dict[str, Any]:
    """Build resonance field for a profile."""
    overlay = build_profile_overlay(acf)
    return build_resonance_field(overlay)


def build_current_profile_matrix_rows(acf: dict[str, Any]) -> list[dict[str, Any]]:
    """Build research matrix rows for current ACF."""
    return build_profile_matrix_rows(acf)