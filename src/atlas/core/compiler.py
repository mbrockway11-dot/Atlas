"""Atlas Core Compiler.

Compiles saved Atlas profile-library artifacts into a CanonicalStructuralSignature.

Compiler passes currently implemented:

1. Identity pass
2. Temporal seed pass
3. ACF pass
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.core.canonical_structural_signature import (
    CanonicalStructuralSignature,
    CipherLayer,
    IdentityLayer,
    KameaLayer,
    TemporalLayer,
)
from atlas.library.profile_library import LIBRARY_DIR


CORE_COMPILER_VERSION = "1.2"


def compile_profile(profile_key: str) -> CanonicalStructuralSignature:
    """Compile one profile into a CanonicalStructuralSignature."""
    profile_payload = safe_load_profile(profile_key)

    identity = build_identity_layer(
        profile_key=profile_key,
        profile_payload=profile_payload,
    )
    temporal = build_temporal_layer(profile_payload=profile_payload)
    cipher = build_cipher_layer(profile_payload=profile_payload)
    kamea = build_kamea_layer(profile_payload=profile_payload)

    return CanonicalStructuralSignature(
        identity=identity,
        cipher=cipher,
        kamea=kamea,
        temporal=temporal,
        metadata={
            "compiler_version": CORE_COMPILER_VERSION,
            "source": "atlas.core.compiler",
            "profile_loaded": bool(profile_payload),
            "acf_loaded": bool(extract_acf(profile_payload)),
        },
    )


def compile_profile_payload(profile_key: str) -> dict[str, Any]:
    """Compile one profile and return a serializable payload."""
    css = compile_profile(profile_key)

    return {
        "success": css.identity is not None,
        "version": CORE_COMPILER_VERSION,
        "profile_key": profile_key,
        "errors": [],
        "warnings": [],
        "data": {
            "canonical_structural_signature": css.to_dict(),
        },
        "metrics": {
            "has_identity": css.identity is not None,
            "has_birth_date": bool(css.identity and css.identity.birth_date),
            "has_birth_time": bool(css.identity and css.identity.birth_time),
            "has_birth_location": bool(css.identity and css.identity.birth_location),
            "has_cipher": has_cipher_data(css.cipher),
            "has_kamea": has_kamea_data(css.kamea),
            "has_temporal": has_temporal_data(css.temporal),
            "has_natal": bool(css.temporal.natal),
            "has_transits": bool(css.temporal.transits),
            "has_dasha": bool(css.temporal.dasha),
            "has_calibration": bool(css.temporal.calibration),
            "has_topology": bool(css.kamea.topology),
            "has_planetary_graphs": bool(css.kamea.planetary_graphs),
            "has_resonance": bool(css.kamea.resonance),
            "has_graph_metrics": bool(css.kamea.graph_metrics),
            "has_fingerprint": bool(css.kamea.fingerprint),
        },
    }


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
        intake.get("aliases")
        or acf_identity.get("aliases")
        or profile_payload.get("aliases")
        or []
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


def build_cipher_layer(*, profile_payload: dict[str, Any]) -> CipherLayer:
    """Build CSS cipher layer from ACF/profile payload."""
    acf = extract_acf(profile_payload)
    cipher_matrix = first_dict(
        acf.get("cipher_matrix"),
        profile_payload.get("cipher_matrix"),
    )

    ciphers = first_dict(
        profile_payload.get("ciphers"),
        profile_payload.get("profile_summary", {}).get("ciphers")
        if isinstance(profile_payload.get("profile_summary"), dict)
        else None,
    )

    ordinal = first_dict(
        cipher_matrix.get("ordinal"),
        ciphers.get("ordinal"),
    )

    hebrew_phonetic = first_dict(
        cipher_matrix.get("hebrew_phonetic"),
        cipher_matrix.get("hebrew"),
        ciphers.get("hebrew_phonetic"),
        ciphers.get("hebrew"),
    )

    hebrew_transliteration = first_dict(
        cipher_matrix.get("hebrew_transliteration"),
        cipher_matrix.get("hebrew_transliteral"),
        ciphers.get("hebrew_transliteration"),
        ciphers.get("hebrew_transliteral"),
    )

    gematria = first_dict(
        cipher_matrix.get("gematria"),
        ciphers.get("gematria"),
    )

    fallback = {
        "cipher_matrix": cipher_matrix,
        "ciphers": ciphers,
        "cipher_status": "compiled_from_saved_profile",
    }

    return CipherLayer(
        ordinal=ordinal or {"source": fallback} if cipher_matrix or ciphers else {},
        hebrew_phonetic=hebrew_phonetic,
        hebrew_transliteration=hebrew_transliteration,
        gematria=gematria,
    )


def build_kamea_layer(*, profile_payload: dict[str, Any]) -> KameaLayer:
    """Build CSS Kamea/topology layer from ACF/profile payload."""
    acf = extract_acf(profile_payload)
    essence_graph = extract_essence_graph(profile_payload)

    identity_graph = first_dict(
        acf.get("identity_graph"),
        essence_graph.get("graph"),
        profile_payload.get("identity_graph"),
        profile_payload.get("graph"),
    )

    planetary_matrix = first_dict(
        acf.get("planetary_matrix"),
        profile_payload.get("planetary_matrix"),
    )

    essence = first_dict(
        acf.get("essence"),
        essence_graph.get("signature"),
        profile_payload.get("essence"),
        profile_payload.get("signature"),
    )

    invariant_analysis = first_dict(
        acf.get("invariant_analysis"),
        profile_payload.get("invariant_analysis"),
    )

    metadata = first_dict(
        acf.get("metadata"),
        profile_payload.get("metadata"),
    )

    fingerprint = first_dict(
        essence.get("fingerprint") if isinstance(essence, dict) else None,
        identity_graph.get("fingerprint") if isinstance(identity_graph, dict) else None,
        metadata.get("fingerprint") if isinstance(metadata, dict) else None,
    )

    return KameaLayer(
        topology={
            **identity_graph,
            "topology_status": "compiled_from_acf",
        }
        if identity_graph
        else {},
        planetary_graphs={
            **planetary_matrix,
            "planetary_status": "compiled_from_acf",
        }
        if planetary_matrix
        else {},
        resonance={
            **essence,
            "resonance_status": "compiled_from_acf",
        }
        if essence
        else {},
        graph_metrics={
            **invariant_analysis,
            "metrics_status": "compiled_from_acf",
        }
        if invariant_analysis
        else {},
        fingerprint=fingerprint,
    )


def build_temporal_layer(*, profile_payload: dict[str, Any]) -> TemporalLayer:
    """Build CSS temporal layer from saved profile payload."""
    temporal = extract_temporal(profile_payload)

    birth = {
        "birth_date": profile_payload.get("birth_date"),
        "birth_time": profile_payload.get("birth_time"),
        "birth_place": profile_payload.get("birth_place"),
        "birth_location": profile_payload.get("birth_location"),
    }
    birth = {
        key: value
        for key, value in birth.items()
        if value is not None
    }

    acf = extract_acf(profile_payload)
    planetary_matrix = first_dict(
        profile_payload.get("planetary_matrix"),
        acf.get("planetary_matrix"),
    )

    natal = first_dict(
        temporal.get("natal"),
        temporal.get("natal_chart"),
        profile_payload.get("natal"),
        profile_payload.get("natal_chart"),
    )

    if birth or planetary_matrix:
        natal = {
            **natal,
            "birth": birth,
            "planetary_matrix": planetary_matrix,
            "temporal_status": "seed_from_saved_profile",
        }

    transits = first_dict(
        temporal.get("transits"),
        temporal.get("transit"),
        profile_payload.get("transits"),
        profile_payload.get("transit"),
    )

    dasha = first_dict(
        temporal.get("dasha"),
        temporal.get("vimshottari_dasha"),
        temporal.get("dashas"),
        profile_payload.get("dasha"),
        profile_payload.get("vimshottari_dasha"),
        profile_payload.get("dashas"),
    )

    calibration = first_dict(
        temporal.get("calibration"),
        profile_payload.get("calibration"),
    )

    return TemporalLayer(
        natal=natal,
        transits=transits,
        dasha=dasha,
        calibration=calibration,
    )


def safe_load_profile(profile_key: str) -> dict[str, Any]:
    """Load a saved profile from the profile library."""
    profile_dir = Path(LIBRARY_DIR) / profile_key

    candidates = [
        profile_dir / "profile.intake.json",
        profile_dir / "profile.acf.json",
        profile_dir / "profile_summary.json",
        profile_dir / "profile_interpretation.json",
        profile_dir / f"{profile_key}_essence_graph.json",
        profile_dir / "profile.json",
        profile_dir / "atlas_profile.json",
        profile_dir / "profile_intake.json",
        profile_dir / "intake.json",
        profile_dir / "acf.json",
    ]

    merged: dict[str, Any] = {}

    for path in candidates:
        data = read_json(path)
        if data:
            merged[path.stem] = data
            merged[normalize_file_key(path.name)] = data
            if isinstance(data, dict):
                merged.update(data)

    return merged


def read_json(path: Path) -> dict[str, Any]:
    """Read JSON if it exists."""
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    if isinstance(data, dict):
        return data

    return {}


def extract_acf(profile_payload: dict[str, Any]) -> dict[str, Any]:
    """Extract ACF data from known profile shapes."""
    candidates = [
        profile_payload.get("profile.acf"),
        profile_payload.get("profile_acf"),
        profile_payload.get("acf"),
        profile_payload.get("atlas_profile"),
        profile_payload.get("data", {}).get("acf")
        if isinstance(profile_payload.get("data"), dict)
        else None,
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate

    if any(
        key in profile_payload
        for key in [
            "analyses",
            "cipher_matrix",
            "essence",
            "identity",
            "identity_graph",
            "identity_persistence",
            "invariant_analysis",
            "planetary_matrix",
        ]
    ):
        return profile_payload

    return {}


def extract_essence_graph(profile_payload: dict[str, Any]) -> dict[str, Any]:
    """Extract saved essence graph data."""
    candidates = [
        profile_payload.get("essence_graph"),
        profile_payload.get("nikola_tesla_essence_graph"),
        profile_payload.get("data", {}).get("essence_graph")
        if isinstance(profile_payload.get("data"), dict)
        else None,
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate

    if "graph" in profile_payload and "signature" in profile_payload:
        return profile_payload

    return {}


def extract_intake(profile_payload: dict[str, Any]) -> dict[str, Any]:
    """Extract intake-like data from known profile shapes."""
    candidates = [
        profile_payload.get("profile.intake"),
        profile_payload.get("profile_intake"),
        profile_payload.get("profile_intake_json"),
        profile_payload.get("intake"),
        profile_payload.get("data", {}).get("intake")
        if isinstance(profile_payload.get("data"), dict)
        else None,
        profile_payload.get("metadata", {}).get("intake")
        if isinstance(profile_payload.get("metadata"), dict)
        else None,
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate

    if any(
        key in profile_payload
        for key in ["birth_date", "birth_place", "birth_time", "name"]
    ):
        return profile_payload

    return {}


def extract_temporal(profile_payload: dict[str, Any]) -> dict[str, Any]:
    """Extract temporal-like data from known profile shapes."""
    candidates = [
        profile_payload.get("temporal"),
        profile_payload.get("temporal_data"),
        profile_payload.get("profile_temporal"),
        profile_payload.get("vedic"),
        profile_payload.get("astrology"),
        profile_payload.get("data", {}).get("temporal")
        if isinstance(profile_payload.get("data"), dict)
        else None,
        profile_payload.get("metadata", {}).get("temporal")
        if isinstance(profile_payload.get("metadata"), dict)
        else None,
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate

    return {}


def extract_birth(
    *,
    intake: dict[str, Any],
    profile_payload: dict[str, Any],
) -> dict[str, str | None]:
    """Extract birth fields from intake/profile payload."""
    birth = intake.get("birth")
    if not isinstance(birth, dict):
        birth = profile_payload.get("birth")

    if not isinstance(birth, dict):
        birth = {}

    birth_date = (
        intake.get("birth_date")
        or birth.get("date")
        or birth.get("birth_date")
        or profile_payload.get("birth_date")
    )

    birth_time = (
        intake.get("birth_time")
        or birth.get("time")
        or birth.get("birth_time")
        or profile_payload.get("birth_time")
    )

    birth_location = (
        intake.get("birth_location")
        or intake.get("birth_place")
        or birth.get("location")
        or birth.get("place")
        or birth.get("birth_location")
        or birth.get("birth_place")
        or profile_payload.get("birth_location")
        or profile_payload.get("birth_place")
    )

    return {
        "birth_date": stringify_or_none(birth_date),
        "birth_time": stringify_or_none(birth_time),
        "birth_location": stringify_or_none(birth_location),
    }


def first_dict(*values: Any) -> dict[str, Any]:
    """Return first dictionary from values."""
    for value in values:
        if isinstance(value, dict):
            return value

    return {}


def has_cipher_data(cipher: CipherLayer) -> bool:
    """Return whether cipher layer has any data."""
    return any(
        [
            bool(cipher.ordinal),
            bool(cipher.hebrew_phonetic),
            bool(cipher.hebrew_transliteration),
            bool(cipher.gematria),
        ]
    )


def has_kamea_data(kamea: KameaLayer) -> bool:
    """Return whether Kamea layer has any data."""
    return any(
        [
            bool(kamea.topology),
            bool(kamea.planetary_graphs),
            bool(kamea.resonance),
            bool(kamea.graph_metrics),
            bool(kamea.fingerprint),
        ]
    )


def has_temporal_data(temporal: TemporalLayer) -> bool:
    """Return whether temporal layer has any data."""
    return any(
        [
            bool(temporal.natal),
            bool(temporal.transits),
            bool(temporal.dasha),
            bool(temporal.calibration),
        ]
    )


def normalize_aliases(value: Any) -> list[str]:
    """Normalize aliases to a list of strings."""
    if value is None:
        return []

    if isinstance(value, str):
        return [value]

    if isinstance(value, list | tuple):
        return [str(item) for item in value if item]

    return []


def normalize_file_key(filename: str) -> str:
    """Normalize file name to a payload key."""
    return (
        filename.replace(".json", "")
        .replace(".", "_")
        .replace("-", "_")
    )


def stringify_or_none(value: Any) -> str | None:
    """Convert value to string or None."""
    if value is None:
        return None

    text = str(value).strip()
    return text or None