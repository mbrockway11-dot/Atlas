"""Temporal Intelligence service layer.

Atlas 3.0 service-backed temporal payloads should read from the canonical
compiler output instead of rebuilding temporal layers manually.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.core.compiler import compile_profile
from atlas.library.profile_library import list_saved_profiles


DEFAULT_PROFILE_DIR = Path("output/library/profiles")
DEFAULT_TRANSIT_DATE = "2026-07-02"


def list_temporal_profiles(
    profile_dir: str | Path = DEFAULT_PROFILE_DIR,
) -> list[dict[str, str]]:
    """Load profile names and slugs for Temporal Intelligence."""
    profiles: list[dict[str, str]] = []

    for profile_key in list_saved_profiles():
        profiles.append(
            {
                "name": profile_key.replace("_", " ").title(),
                "slug": profile_key,
            }
        )

    return profiles


def build_temporal_intelligence_payload(
    profile_key: str,
    profile_dir: str | Path = DEFAULT_PROFILE_DIR,
    *,
    transit_date: str = DEFAULT_TRANSIT_DATE,
) -> dict[str, Any]:
    """Build canonical temporal intelligence payload from compiled CSS."""
    try:
        css = compile_profile(profile_key).to_dict()
    except Exception as exc:  # noqa: BLE001
        return failure_payload(
            profile_key=profile_key,
            profile_path=Path(profile_dir) / profile_key,
            transit_date=transit_date,
            error=f"Profile compilation failed: {exc}",
        )

    temporal = css.get("temporal", {})
    natal = temporal.get("natal", {})
    ephemeris = natal.get("ephemeris", {})

    if not ephemeris:
        return failure_payload(
            profile_key=profile_key,
            profile_path=Path(profile_dir) / profile_key,
            transit_date=transit_date,
            error="Compiled profile has no temporal ephemeris payload.",
        )

    exports = {
        "css_temporal": temporal,
        "birth": ephemeris.get("birth", {}),
        "natal": ephemeris,
        "sidereal": ephemeris.get("sidereal", {}),
        "houses": ephemeris.get("houses", {}),
        "nakshatras": ephemeris.get("nakshatra", {}),
        "dignity": ephemeris.get("dignity", {}),
        "aspects": ephemeris.get("aspects", {}),
        "yogas": ephemeris.get("yogas", {}),
        "navamsa": ephemeris.get("navamsa", {}),
        "vargas": ephemeris.get("vargas", {}),
        "dasha": ephemeris.get("vimshottari_dasha", {}),
        "transits": ephemeris.get("transits", {}),
    }

    warnings = build_temporal_warnings(exports)

    return {
        "success": True,
        "profile_key": profile_key,
        "profile_dir": str(Path(profile_dir) / profile_key),
        "transit_date": transit_date,
        "errors": [],
        "warnings": warnings,
        "data": exports,
        "exports": exports,
        "metrics": build_temporal_metrics(exports),
    }


def build_temporal_metrics(
    exports: dict[str, Any],
) -> dict[str, Any]:
    """Build summary metrics for dashboard rendering."""
    birth = exports.get("birth", {})
    natal = exports.get("natal", {})
    sidereal = exports.get("sidereal", {})
    houses = exports.get("houses", {})
    nakshatras = exports.get("nakshatras", {})
    dignity = exports.get("dignity", {})
    aspects = exports.get("aspects", {})
    yogas = exports.get("yogas", {})
    navamsa = exports.get("navamsa", {})
    dasha = exports.get("dasha", {})
    transits = exports.get("transits", {})

    return {
        "birth_date": birth.get("date", birth.get("birth_date", "")),
        "birth_time": birth.get("time", birth.get("birth_time", "Unknown")),
        "birth_place": birth.get("place", birth.get("birth_place", "")),
        "planet_count": len(natal.get("planets", {})),
        "sidereal_status": natal.get("sidereal_status", ""),
        "nakshatra_status": natal.get("nakshatra_status", ""),
        "houses_status": natal.get("houses_status", ""),
        "aspects_status": natal.get("aspects_status", ""),
        "dignity_status": natal.get("dignity_status", ""),
        "navamsa_status": natal.get("navamsa_status", ""),
        "vargas_status": natal.get("vargas_status", ""),
        "yogas_status": natal.get("yogas_status", ""),
        "vimshottari_dasha_status": natal.get("vimshottari_dasha_status", ""),
        "transits_status": natal.get("transits_status", ""),
        "house_count": _summary_count(houses, "house_count", "houses"),
        "nakshatra_count": _summary_count(nakshatras, "planet_count", "positions"),
        "dignity_count": _summary_count(dignity, "planet_count", "dignities"),
        "aspect_count": _summary_count(aspects, "aspect_count", "aspects"),
        "yoga_count": _summary_count(yogas, "matched", "matches"),
        "navamsa_count": _summary_count(navamsa, "planet_count", "positions"),
        "dasha_periods": _summary_count(dasha, "period_count", "periods"),
        "transit_contacts": _summary_count(transits, "contact_count", "contacts"),
        "moon_nakshatra": _moon_nakshatra(nakshatras),
        "zodiac": sidereal.get("zodiac", natal.get("zodiac", "")),
    }


def build_temporal_warnings(
    exports: dict[str, Any],
) -> list[str]:
    """Build temporal warnings from canonical payload."""
    warnings: list[str] = []
    metrics = build_temporal_metrics(exports)

    if not metrics.get("moon_nakshatra"):
        warnings.append(
            "Moon nakshatra could not be resolved; dasha output may be limited."
        )

    for key in [
        "sidereal_status",
        "nakshatra_status",
        "houses_status",
        "aspects_status",
        "dignity_status",
        "navamsa_status",
        "yogas_status",
        "vimshottari_dasha_status",
        "transits_status",
    ]:
        if metrics.get(key) not in {"computed", ""}:
            warnings.append(f"{key}={metrics.get(key)}")

    return warnings


def _summary_count(
    payload: dict[str, Any],
    summary_key: str,
    collection_key: str,
) -> int:
    """Read count from summary, then fall back to collection length."""
    summary = payload.get("summary", {})
    value = summary.get(summary_key)

    if isinstance(value, int):
        return value

    collection = payload.get(collection_key, {})

    if isinstance(collection, dict):
        return len(collection)

    if isinstance(collection, list):
        return len(collection)

    return 0


def _moon_nakshatra(
    nakshatras: dict[str, Any],
) -> str:
    """Return Moon nakshatra from canonical nakshatra payload."""
    positions = nakshatras.get("positions", {})

    if isinstance(positions, dict):
        moon = positions.get("Moon", {})
        if isinstance(moon, dict):
            return str(moon.get("nakshatra", ""))

    placements = nakshatras.get("placements", [])

    if isinstance(placements, list):
        for placement in placements:
            if placement.get("planet") == "Moon":
                return str(placement.get("nakshatra", ""))

    return ""


def json_export(data: Any) -> str:
    """Serialize JSON exports."""
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def failure_payload(
    *,
    profile_key: str,
    profile_path: Path,
    transit_date: str,
    error: str,
) -> dict[str, Any]:
    """Build failure payload."""
    return {
        "success": False,
        "profile_key": profile_key,
        "profile_dir": str(profile_path),
        "transit_date": transit_date,
        "errors": [error],
        "warnings": [],
        "data": {},
        "exports": {},
        "metrics": {},
    }
