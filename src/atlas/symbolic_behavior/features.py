"""Extract stable symbolic features while preserving shared-input dependencies."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.services.profile_path_service import resolve_profile_dir


BIRTH_DATE_NUMBERS = {"life_path", "birthday", "attitude", "birth_month", "birth_year"}
NAME_NUMBERS = {"expression", "soul_urge", "personality", "balance"}
SUPPORTED_PLANETS = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu")


def extract_symbolic_feature_matrix(profile_keys: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    features: list[dict[str, Any]] = []
    quality: list[dict[str, Any]] = []
    for profile_key in sorted(set(profile_keys)):
        rows, report = extract_profile_features(profile_key)
        features.extend(rows)
        quality.append(report)
    return features, quality


def extract_profile_features(profile_key: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    profile_dir = resolve_profile_dir(profile_key)
    codex = read_json(profile_dir / "structural_codex.json")
    payload = read_json(profile_dir / "profile.payload.json")
    if not codex or not payload:
        return [], {
            "profile_key": profile_key, "success": False,
            "errors": ["structural_codex.json or profile.payload.json is missing"],
            "feature_count": 0,
        }
    rows: list[dict[str, Any]] = []
    temporal = payload.get("temporal", {}) or {}
    natal = temporal.get("natal", {}) or {}
    sidereal = natal.get("sidereal", {}) or {}
    planets = sidereal.get("planets", {}) or {}
    time_known = bool((temporal.get("summary", {}) or {}).get("time_known"))
    for planet in SUPPORTED_PLANETS:
        record = planets.get(planet) or planets.get(planet.casefold())
        if not isinstance(record, dict):
            continue
        add(rows, profile_key, f"vedic.{planet.casefold()}.sign", "vedic", "birth_input", "categorical", record.get("sign"), f"temporal.natal.sidereal.planets.{planet}.sign", ["birth_date", "birth_place"])
        add(rows, profile_key, f"vedic.{planet.casefold()}.retrograde", "vedic", "birth_input", "categorical", bool(record.get("retrograde")), f"temporal.natal.sidereal.planets.{planet}.retrograde", ["birth_date"])

    symbolic = codex.get("symbolic_profile", {}) or {}
    numerology = symbolic.get("numerology", {}) or {}
    for key, record in (numerology.get("core_numbers", {}) or {}).items():
        if not isinstance(record, dict) or record.get("number") is None:
            continue
        if key in BIRTH_DATE_NUMBERS:
            group, dependencies = "birth_input", ["birth_date"]
        elif key in NAME_NUMBERS:
            group, dependencies = "name_input", ["recorded_name"]
        else:
            group, dependencies = "birth_and_name_input", ["birth_date", "recorded_name"]
        add(rows, profile_key, f"numerology.{key}.number", "numerology", group, "categorical", record["number"], f"symbolic_profile.numerology.core_numbers.{key}.number", dependencies)

    gematria = symbolic.get("gematria", {}) or {}
    for system, record in (gematria.get("systems", {}) or {}).items():
        if isinstance(record, dict):
            add(rows, profile_key, f"gematria.{system}.digital_root", "gematria", "name_input", "categorical", record.get("digital_root"), f"symbolic_profile.gematria.systems.{system}.digital_root", ["recorded_name"])
    cross = gematria.get("cross_system", {}) or {}
    add(rows, profile_key, "gematria.cross_system.distinct_root_count", "gematria", "name_input", "numeric", cross.get("distinct_root_count"), "symbolic_profile.gematria.cross_system.distinct_root_count", ["recorded_name"])
    add(rows, profile_key, "gematria.cross_system.exact_root_convergence", "gematria", "name_input", "categorical", cross.get("exact_root_convergence"), "symbolic_profile.gematria.cross_system.exact_root_convergence", ["recorded_name"])

    kamea = symbolic.get("kamea", {}) or {}
    ranked = kamea.get("ranked_planets", []) or []
    if ranked:
        add(rows, profile_key, "kamea.top_planet", "kamea", "name_input", "categorical", ranked[0].get("planet"), "symbolic_profile.kamea.ranked_planets[0].planet", ["recorded_name", "cipher_rules"])
    for record in ranked:
        planet = str(record.get("planet") or "").casefold()
        if planet:
            add(rows, profile_key, f"kamea.{planet}.composite_score", "kamea", "name_input", "numeric", record.get("composite_score"), f"symbolic_profile.kamea.ranked_planets.{planet}.composite_score", ["recorded_name", "cipher_rules"])
    return rows, {
        "profile_key": profile_key,
        "success": bool(rows),
        "birth_time_known": time_known,
        "houses_included": False,
        "feature_count": len(rows),
        "families": sorted({row["feature_family"] for row in rows}),
        "independence_groups": sorted({row["independence_group"] for row in rows}),
        "errors": [],
        "warnings": [] if time_known else ["Birth time unknown; houses and angles are excluded."],
    }


def add(rows: list[dict[str, Any]], profile_key: str, feature_id: str, family: str, independence_group: str, value_type: str, value: Any, source_path: str, dependencies: list[str]) -> None:
    if value is None or value == "":
        return
    rows.append({
        "profile_key": profile_key, "feature_id": feature_id,
        "feature_family": family, "independence_group": independence_group,
        "value_type": value_type, "value": value,
        "source_path": source_path, "input_dependencies": dependencies,
        "claim_type": "deterministic_symbolic_feature", "empirical_evidence": False,
    })


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
