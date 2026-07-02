"""Identity pass for the CSS compiler."""

from __future__ import annotations

from typing import Any

from atlas.core.canonical_structural_signature import IdentityLayer
from atlas.core.compiler_passes.utils import (
    extract_acf,
    extract_birth,
    extract_intake,
    first_dict,
    normalize_aliases,
)


def build_identity_layer(
    *,
    profile_key: str,
    profile_payload: dict[str, Any],
) -> IdentityLayer:
    """Build CSS identity layer from saved profile data."""
    intake = extract_intake(profile_payload)
    acf = extract_acf(profile_payload)
    acf_identity = first_dict(acf.get("identity"))

    canonical_name = (
        intake.get("name")
        or intake.get("canonical_name")
        or acf_identity.get("name")
        or acf_identity.get("canonical_name")
        or profile_payload.get("name")
        or profile_payload.get("canonical_name")
        or profile_payload.get("display_name")
        or profile_key.replace("_", " ").title()
    )

    aliases = normalize_aliases(
        intake.get("aliases") or acf_identity.get("aliases") or profile_payload.get("aliases") or []
    )

    birth = extract_birth(intake=intake, profile_payload=profile_payload)

    return IdentityLayer(
        profile_key=profile_key,
        canonical_name=str(canonical_name),
        aliases=aliases,
        birth_date=birth.get("birth_date"),
        birth_time=birth.get("birth_time"),
        birth_location=birth.get("birth_location"),
        metadata={
            "identity_source": "profile_library",
            "has_profile_payload": bool(profile_payload),
            "has_intake": bool(intake),
            "has_acf_identity": bool(acf_identity),
        },
    )