"""Atlas Identity Bridge.

Build one unified profile object that connects structural and temporal layers.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
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


IDENTITY_BRIDGE_VERSION = "1.0"


@dataclass(frozen=True)
class AtlasIdentity:
    """Unified Atlas identity object."""

    version: str
    name: str
    profile_path: str
    acf: dict[str, Any]
    intake: dict[str, Any]
    temporal: dict[str, Any]
    summary: dict[str, Any]


def build_atlas_identity(
    profile_dir: Path,
    *,
    transit_date: str | None = None,
) -> AtlasIdentity:
    """Build unified Atlas identity from a profile directory."""

    acf = load_json_file(profile_dir / "profile.acf.json")
    intake = load_json_file(profile_dir / "profile.intake.json")

    birth = load_birth_data_from_profile(profile_dir)

    temporal = build_temporal_payload(
        profile_dir=profile_dir,
        transit_date=transit_date,
    )

    name = (
        intake.get("name")
        or acf.get("identity", {}).get("name")
        or birth.name
        or profile_dir.name
    )

    return AtlasIdentity(
        version=IDENTITY_BRIDGE_VERSION,
        name=name,
        profile_path=str(profile_dir),
        acf=acf,
        intake=intake,
        temporal=temporal,
        summary={
            "name": name,
            "has_acf": bool(acf),
            "has_intake": bool(intake),
            "has_birth_date": bool(birth.birth_date),
            "time_known": birth.time_known,
            "temporal_layers": sorted(temporal.keys()),
        },
    )


def build_temporal_payload(
    *,
    profile_dir: Path,
    transit_date: str | None = None,
) -> dict[str, Any]:
    """Build all temporal layers for one profile."""

    birth = load_birth_data_from_profile(profile_dir)

    if not birth.birth_date:
        return {
            "birth": asdict(birth),
            "error": "Missing birth date.",
        }

    natal = build_natal_chart(birth)
    houses = build_house_chart(natal)
    nakshatras = build_nakshatra_chart(natal)
    dignity = build_dignity_chart(natal)
    aspects = build_aspect_chart(houses)
    yogas = evaluate_all_yogas(
        natal=natal,
        houses=houses,
        dignity=dignity,
        aspects=aspects,
    )
    navamsa = build_navamsa_chart(natal)
    dasha = build_vimshottari_dasha(
        name=birth.name,
        birth_date=birth.birth_date,
        nakshatra_chart=nakshatras,
    )
    transits = build_transit_chart(
        natal,
        transit_date=transit_date,
    )

    return {
        "birth": asdict(birth),
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


def load_json_file(
    path: Path,
) -> dict[str, Any]:
    """Load JSON file if present."""

    if not path.exists():
        return {}

    return json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )


def atlas_identity_to_dict(
    identity: AtlasIdentity,
) -> dict[str, Any]:
    """Convert AtlasIdentity to dictionary."""

    return {
        "version": identity.version,
        "name": identity.name,
        "profile_path": identity.profile_path,
        "acf": identity.acf,
        "intake": identity.intake,
        "temporal": identity.temporal,
        "summary": identity.summary,
    }


def export_atlas_identity(
    identity: AtlasIdentity,
    output_path: Path,
) -> None:
    """Export unified Atlas identity JSON."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            atlas_identity_to_dict(identity),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )