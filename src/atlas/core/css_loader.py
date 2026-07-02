"""Canonical Structural Signature runtime loader.

Provides the runtime API for loading compiled CSS artifacts from output/css.
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
    PopulationLayer,
    ResearchLayer,
    TemporalLayer,
    ValidationLayer,
)


DEFAULT_CSS_DIR = Path("output") / "css"
CSS_INDEX_FILENAME = "css_index.json"


def load_css_payload(
    profile_key: str,
    *,
    css_dir: str | Path = DEFAULT_CSS_DIR,
) -> dict[str, Any]:
    """Load one compiled CSS artifact payload."""
    path = css_path(profile_key=profile_key, css_dir=css_dir)

    if not path.exists():
        raise FileNotFoundError(f"CSS artifact not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"CSS artifact is not a JSON object: {path}")

    return data


def load_css(
    profile_key: str,
    *,
    css_dir: str | Path = DEFAULT_CSS_DIR,
) -> CanonicalStructuralSignature:
    """Load one compiled CSS artifact as a CanonicalStructuralSignature."""
    payload = load_css_payload(profile_key, css_dir=css_dir)
    css_data = payload.get("css")

    if not isinstance(css_data, dict):
        raise ValueError(f"CSS payload missing css object for: {profile_key}")

    return css_from_dict(css_data)


def list_compiled_css(
    *,
    css_dir: str | Path = DEFAULT_CSS_DIR,
) -> list[str]:
    """List compiled CSS profile keys."""
    index = load_css_index(css_dir=css_dir)

    profiles = index.get("profiles", [])
    if not isinstance(profiles, list):
        return []

    keys = [
        item.get("profile_key")
        for item in profiles
        if isinstance(item, dict) and item.get("success") and item.get("profile_key")
    ]

    return sorted(str(item) for item in keys)


def load_css_index(
    *,
    css_dir: str | Path = DEFAULT_CSS_DIR,
) -> dict[str, Any]:
    """Load CSS export index."""
    path = Path(css_dir) / CSS_INDEX_FILENAME

    if not path.exists():
        raise FileNotFoundError(f"CSS index not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"CSS index is not a JSON object: {path}")

    return data


def css_exists(
    profile_key: str,
    *,
    css_dir: str | Path = DEFAULT_CSS_DIR,
) -> bool:
    """Return whether a compiled CSS artifact exists."""
    return css_path(profile_key=profile_key, css_dir=css_dir).exists()


def css_path(
    *,
    profile_key: str,
    css_dir: str | Path = DEFAULT_CSS_DIR,
) -> Path:
    """Return compiled CSS artifact path."""
    return Path(css_dir) / f"{profile_key}.css.json"


def css_from_dict(data: dict[str, Any]) -> CanonicalStructuralSignature:
    """Rehydrate a CanonicalStructuralSignature from dictionary data."""
    return CanonicalStructuralSignature(
        version=str(data.get("version", "1.0")),
        identity=identity_from_dict(data.get("identity")),
        cipher=CipherLayer(**dict_or_empty(data.get("cipher"))),
        kamea=KameaLayer(**dict_or_empty(data.get("kamea"))),
        temporal=TemporalLayer(**dict_or_empty(data.get("temporal"))),
        validation=ValidationLayer(**dict_or_empty(data.get("validation"))),
        research=ResearchLayer(**dict_or_empty(data.get("research"))),
        population=PopulationLayer(**dict_or_empty(data.get("population"))),
        metadata=dict_or_empty(data.get("metadata")),
    )


def identity_from_dict(value: Any) -> IdentityLayer | None:
    """Rehydrate IdentityLayer from dictionary data."""
    if not isinstance(value, dict):
        return None

    return IdentityLayer(
        profile_key=str(value.get("profile_key", "")),
        canonical_name=str(value.get("canonical_name", "")),
        aliases=list(value.get("aliases", []))
        if isinstance(value.get("aliases"), list)
        else [],
        birth_date=string_or_none(value.get("birth_date")),
        birth_time=string_or_none(value.get("birth_time")),
        birth_location=string_or_none(value.get("birth_location")),
        metadata=dict_or_empty(value.get("metadata")),
    )


def dict_or_empty(value: Any) -> dict[str, Any]:
    """Return value if dict, else empty dict."""
    return value if isinstance(value, dict) else {}


def string_or_none(value: Any) -> str | None:
    """Return string or None."""
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def json_export(data: Any) -> str:
    """Serialize JSON."""
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)