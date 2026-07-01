"""Temporal Intelligence service layer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.temporal.aspects import aspect_chart_to_dict, build_aspect_chart
from atlas.temporal.birth import load_birth_data_from_profile
from atlas.temporal.dignity import build_dignity_chart, dignity_chart_to_dict
from atlas.temporal.houses import build_house_chart, house_chart_to_dict
from atlas.temporal.nakshatra import build_nakshatra_chart, nakshatra_chart_to_dict
from atlas.temporal.natal_chart import build_natal_chart, natal_chart_to_dict
from atlas.temporal.navamsa import build_navamsa_chart, navamsa_chart_to_dict
from atlas.temporal.transits import build_transit_chart, transit_chart_to_dict
from atlas.temporal.vimshottari_dasha import (
    build_vimshottari_dasha,
    vimshottari_dasha_to_dict,
)
from atlas.temporal.yoga_engine import evaluate_all_yogas, yoga_evaluation_to_dict


DEFAULT_PROFILE_DIR = Path("output/library/profiles")
DEFAULT_TRANSIT_DATE = "2026-06-29"


def list_temporal_profiles(profile_dir: str | Path = DEFAULT_PROFILE_DIR) -> list[dict[str, str]]:
    """Load profile names and slugs for Temporal Intelligence."""
    root = Path(profile_dir)

    if not root.exists():
        return []

    profiles: list[dict[str, str]] = []

    for profile_path in sorted(root.iterdir()):
        if not profile_path.is_dir():
            continue

        intake_path = profile_path / "profile.intake.json"
        name = profile_path.name

        if intake_path.exists():
            try:
                intake = json.loads(intake_path.read_text(encoding="utf-8"))
                name = intake.get("name", profile_path.name)
            except json.JSONDecodeError:
                name = profile_path.name

        profiles.append(
            {
                "name": name,
                "slug": profile_path.name,
            }
        )

    return profiles


def build_temporal_intelligence_payload(
    profile_key: str,
    profile_dir: str | Path = DEFAULT_PROFILE_DIR,
    *,
    transit_date: str = DEFAULT_TRANSIT_DATE,
) -> dict[str, Any]:
    """Build all temporal layers for one profile."""
    root = Path(profile_dir)
    profile_path = root / profile_key

    if not profile_path.exists():
        return {
            "success": False,
            "profile_key": profile_key,
            "profile_dir": str(profile_path),
            "transit_date": transit_date,
            "errors": [f"Profile not found: {profile_path}"],
            "warnings": [],
            "data": {},
            "exports": {},
            "metrics": {},
        }

    birth = load_birth_data_from_profile(profile_path)

    if not birth.birth_date:
        return {
            "success": False,
            "profile_key": profile_key,
            "profile_dir": str(profile_path),
            "transit_date": transit_date,
            "errors": ["Selected profile has no birth date."],
            "warnings": [],
            "data": {"birth": birth},
            "exports": {},
            "metrics": {},
        }

    natal = build_natal_chart(birth)
    houses = build_house_chart(natal)
    nakshatras = build_nakshatra_chart(natal)
    dignity = build_dignity_chart(natal)
    aspects = build_aspect_chart(houses)
    yogas = evaluate_all_yogas(natal, houses, dignity, aspects)
    navamsa = build_navamsa_chart(natal)
    dasha = build_vimshottari_dasha(
        moon_nakshatra=natal.moon_nakshatra,
        birth_date=birth.birth_date,
    )
    transits = build_transit_chart(
        natal,
        transit_date=transit_date,
    )

    exports = {
        "natal": natal_chart_to_dict(natal),
        "houses": house_chart_to_dict(houses),
        "nakshatras": nakshatra_chart_to_dict(nakshatras),
        "dignity": dignity_chart_to_dict(dignity),
        "aspects": aspect_chart_to_dict(aspects),
        "yogas": yoga_evaluation_to_dict(yogas),
        "navamsa": navamsa_chart_to_dict(navamsa),
        "dasha": vimshottari_dasha_to_dict(dasha),
        "transits": transit_chart_to_dict(transits),
    }

    return {
        "success": True,
        "profile_key": profile_key,
        "profile_dir": str(profile_path),
        "transit_date": transit_date,
        "errors": [],
        "warnings": [],
        "data": {
            "birth": birth,
            "natal": natal,
            "houses": houses,
            "nakshatras": nakshatras,
            "dignity": dignity,
            "aspects": aspects,
            "yogas": yogas,
            "navamsa": navamsa,
            "dasha": dasha,
            "transits": transits,
        },
        "exports": exports,
        "metrics": build_temporal_metrics(
            birth,
            natal,
            houses,
            nakshatras,
            dignity,
            yogas,
            dasha,
            transits,
        ),
    }


def build_temporal_metrics(
    birth: Any,
    natal: Any,
    houses: Any,
    nakshatras: Any,
    dignity: Any,
    yogas: Any,
    dasha: Any,
    transits: Any,
) -> dict[str, Any]:
    """Build summary metrics for dashboard rendering."""
    return {
        "birth_date": birth.birth_date,
        "birth_time": birth.birth_time or "Unknown",
        "birth_place": birth.birth_place or "",
        "planet_count": len(getattr(natal, "planets", [])),
        "house_count": len(getattr(houses, "houses", [])),
        "nakshatra_count": len(getattr(nakshatras, "placements", [])),
        "dignity_count": len(getattr(dignity, "placements", [])),
        "yoga_count": len(getattr(yogas, "yogas", [])),
        "dasha_periods": len(getattr(dasha, "periods", [])),
        "transit_contacts": transits.summary.get("contact_count", 0),
        "transit_aspects": aspects_count_safe(transits),
    }


def json_export(data: Any) -> str:
    """Serialize JSON exports."""
    return json.dumps(data, indent=2, sort_keys=True)


def aspects_count_safe(transits: Any) -> int:
    """Return transit aspect count from summary fields."""
    summary = getattr(transits, "summary", {}) or {}
    return (
        summary.get("opposition_count", 0)
        + summary.get("conjunction_count", 0)
        + summary.get("trine_count", 0)
        + summary.get("square_count", 0)
    )