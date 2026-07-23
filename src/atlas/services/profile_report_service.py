"""Canonical Profile Report service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.intelligence import (
    atlas_interpretation_to_dict,
    atlas_report_to_dict,
    build_atlas_report,
    interpret_identity,
)
from atlas.intelligence.profile import AtlasProfile
from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles
from atlas.services.graph_service import build_identity_stack_payload
from atlas.services.profile_library_service import load_profile_library_payload
from atlas.services.temporal_intelligence_service import (
    DEFAULT_TRANSIT_DATE,
    build_temporal_intelligence_payload,
)


def list_profile_report_profiles() -> list[str]:
    return list_saved_profiles()


def build_profile_report_payload(
    profile_key: str,
    *,
    transit_date: str = DEFAULT_TRANSIT_DATE,
) -> dict[str, Any]:
    profile_dir = LIBRARY_DIR / profile_key

    if not profile_dir.exists():
        return failure_payload(profile_key, f"Profile directory not found: {profile_dir}")

    library_payload = load_profile_library_payload(profile_key)

    temporal_payload = build_temporal_intelligence_payload(
        profile_key,
        LIBRARY_DIR,
        transit_date=transit_date,
    )

    graph_payload = build_identity_stack_payload(profile_key)

    atlas_profile = build_atlas_profile(
        profile_key=profile_key,
        profile_dir=profile_dir,
        library_payload=library_payload,
        temporal_payload=temporal_payload,
        graph_payload=graph_payload,
    )

    identity = build_interpreter_identity(atlas_profile)
    interpretation = interpret_identity(identity)
    report = build_atlas_report(interpretation)

    interpretation_dict = atlas_interpretation_to_dict(interpretation)
    report_dict = atlas_report_to_dict(report)

    payload: dict[str, Any] = {
        "success": True,
        "profile_key": profile_key,
        "profile_dir": str(profile_dir),
        "transit_date": transit_date,
        "errors": collect_errors(library_payload, temporal_payload, graph_payload),
        "warnings": collect_warnings(library_payload, temporal_payload, graph_payload),
        "data": {
            "atlas_profile": atlas_profile.to_dict(),
            "library": library_payload,
            "temporal": strip_runtime_objects(temporal_payload),
            "graph": strip_runtime_objects(graph_payload),
            "interpretation": interpretation_dict,
            "report": report_dict,
        },
        "exports": {
            "markdown": report.markdown,
            "report_json": report_dict,
            "interpretation_json": interpretation_dict,
        },
        "metrics": build_report_metrics(
            library_payload=library_payload,
            temporal_payload=temporal_payload,
            graph_payload=graph_payload,
            interpretation=interpretation_dict,
            report=report_dict,
        ),
    }

    payload["exports"]["full_payload_json"] = make_json_safe_for_export(payload)
    return payload


def build_atlas_profile(
    *,
    profile_key: str,
    profile_dir: Path,
    library_payload: dict[str, Any],
    temporal_payload: dict[str, Any],
    graph_payload: dict[str, Any],
) -> AtlasProfile:
    display_name = resolve_display_name(profile_key, library_payload)

    profile = AtlasProfile(
        profile_key=profile_key,
        display_name=display_name,
        profile_dir=str(profile_dir),
    )

    profile = profile.with_section("library", library_payload)
    profile = profile.with_section("temporal", strip_runtime_objects(temporal_payload))
    profile = profile.with_section("graph", strip_runtime_objects(graph_payload))

    if library_payload.get("acf") is not None:
        profile = profile.with_section("acf", library_payload.get("acf"))

    if library_payload.get("intake") is not None:
        profile = profile.with_section("intake", library_payload.get("intake"))

    profile = profile.with_evidence(build_report_evidence(profile_key))
    profile = profile.with_provenance(build_report_provenance())

    for warning in collect_warnings(library_payload, temporal_payload, graph_payload):
        profile = profile.with_warning(warning)

    return profile


class InterpreterIdentity:
    """Compatibility adapter for atlas.intelligence.interpreter."""

    def __init__(self, profile: AtlasProfile) -> None:
        payload = profile.to_dict()
        sections = payload.get("sections", {})

        self.name = profile.display_name
        self.summary = {
            "profile_key": profile.profile_key,
            "profile_dir": profile.profile_dir,
            "has_acf": bool(sections.get("acf")),
            "has_intake": bool(sections.get("intake")),
            "has_temporal": bool(sections.get("temporal")),
            "has_graph": bool(sections.get("graph")),
        }
        self.intake = sections.get("intake", {})
        self.acf = sections.get("acf", {})
        self.temporal = normalize_temporal_for_interpreter(sections.get("temporal", {}))
        self.graph = sections.get("graph", {})


def build_interpreter_identity(profile: AtlasProfile) -> InterpreterIdentity:
    return InterpreterIdentity(profile)


def normalize_temporal_for_interpreter(
    temporal_payload: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(temporal_payload, dict):
        return {}

    exports = temporal_payload.get("exports", {})

    if exports:
        # The intelligence interpreter explicitly describes these placements as
        # sidereal.  Passing the full ephemeris here silently supplied tropical
        # planets under a Vedic label.  Prefer the canonical sidereal chart and
        # retain the tropical chart under an explicit key for consumers that
        # genuinely need it.
        sidereal = exports.get("sidereal", {})
        return {
            "birth": exports.get("birth", {}),
            "natal": sidereal or exports.get("natal", {}),
            "tropical_natal": exports.get("natal", {}),
            "zodiac": "sidereal" if sidereal else exports.get("natal", {}).get("zodiac", "unknown"),
            "houses": exports.get("houses", {}),
            "nakshatras": exports.get("nakshatras", {}),
            "dignity": exports.get("dignity", {}),
            "aspects": exports.get("aspects", {}),
            "yogas": exports.get("yogas", {}),
            "navamsa": exports.get("navamsa", {}),
            "dasha": exports.get("dasha", {}),
            "transits": exports.get("transits", {}),
            "metrics": temporal_payload.get("metrics", {}),
        }

    return temporal_payload


def resolve_display_name(profile_key: str, library_payload: dict[str, Any]) -> str:
    intake = library_payload.get("intake") or {}
    acf = library_payload.get("acf") or {}

    if isinstance(intake, dict) and intake.get("name"):
        return str(intake["name"])

    if isinstance(acf, dict) and acf.get("name"):
        return str(acf["name"])

    identity = acf.get("identity") if isinstance(acf, dict) else None
    if isinstance(identity, dict) and identity.get("name"):
        return str(identity["name"])

    return profile_key.replace("_", " ").title()


def build_report_metrics(
    *,
    library_payload: dict[str, Any],
    temporal_payload: dict[str, Any],
    graph_payload: dict[str, Any],
    interpretation: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, Any]:
    return {
        "has_acf": library_payload.get("acf") is not None,
        "has_intake": library_payload.get("intake") is not None,
        "has_temporal": temporal_payload.get("success", False),
        "has_graph": graph_payload.get("success", False),
        "section_count": len(interpretation.get("sections", [])),
        "report_word_count": len(str(report.get("markdown", "")).split()),
        "missing_artifacts": library_payload.get("missing", []),
        "temporal_metrics": temporal_payload.get("metrics", {}),
        "graph_metrics": graph_payload.get("metrics", {}),
    }


def collect_errors(*payloads: dict[str, Any]) -> list[Any]:
    errors: list[Any] = []
    for payload in payloads:
        errors.extend(payload.get("errors", []))
    return errors


def collect_warnings(*payloads: dict[str, Any]) -> list[str]:
    warnings: list[str] = []

    for payload in payloads:
        warnings.extend(str(item) for item in payload.get("warnings", []))

    library_payload = payloads[0] if payloads else {}
    for missing in library_payload.get("missing", []):
        warnings.append(f"Missing artifact: {missing}")

    return warnings


def build_report_evidence(profile_key: str) -> list[dict[str, Any]]:
    return [
        {
            "source": "profile_report_service",
            "profile_key": profile_key,
            "role": "Assembles profile library, temporal intelligence, and graph stack.",
        }
    ]


def build_report_provenance() -> list[dict[str, Any]]:
    return [
        {
            "source": "atlas.services.profile_library_service",
            "role": "Loads profile artifacts.",
        },
        {
            "source": "atlas.services.temporal_intelligence_service",
            "role": "Builds natal, dasha, transit, and temporal layers.",
        },
        {
            "source": "atlas.services.graph_service",
            "role": "Builds identity stack, topology, resonance, and graph audit.",
        },
        {
            "source": "atlas.intelligence.interpreter",
            "role": "Interprets assembled AtlasProfile.",
        },
        {
            "source": "atlas.intelligence.report",
            "role": "Renders interpreted profile into report format.",
        },
    ]


def strip_runtime_objects(payload: dict[str, Any]) -> dict[str, Any]:
    clean = dict(payload)

    if "data" in clean:
        clean["data"] = {
            key: make_json_safe_for_export(value)
            for key, value in clean.get("data", {}).items()
            if is_json_safe(value) or hasattr(value, "__dict__")
        }

    return clean


def is_json_safe(value: Any) -> bool:
    try:
        json.dumps(value)
        return True
    except TypeError:
        return False


def make_json_safe_for_export(value: Any) -> Any:
    if is_json_safe(value):
        return value

    if isinstance(value, dict):
        return {str(key): make_json_safe_for_export(item) for key, item in value.items()}

    if isinstance(value, list):
        return [make_json_safe_for_export(item) for item in value]

    if hasattr(value, "__dict__"):
        return {
            str(key): make_json_safe_for_export(item)
            for key, item in value.__dict__.items()
        }

    return str(value)


def failure_payload(profile_key: str, message: str) -> dict[str, Any]:
    return {
        "success": False,
        "profile_key": profile_key,
        "errors": [message],
        "warnings": [],
        "data": {},
        "exports": {},
        "metrics": {},
    }


def json_export(data: Any) -> str:
    return json.dumps(make_json_safe_for_export(data), indent=2, sort_keys=True)
