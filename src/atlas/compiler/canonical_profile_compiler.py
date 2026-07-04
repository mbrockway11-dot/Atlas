"""Canonical Atlas profile compiler.

Single source of truth for profile compilation.

Input:
    profile.intake.json

Output:
    profile.payload.json

ACF is legacy/export only and should not be required by new services.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from atlas.services.profile_path_service import resolve_profile_dir
from atlas.temporal.birth import build_birth_data_from_intake
from atlas.temporal.natal_chart import build_natal_chart_payload
from atlas.interpretation.profile_classifier import classify_profile


CANONICAL_PROFILE_COMPILER_VERSION = "1.0"


def compile_canonical_profile(profile_key: str, *, force: bool = False) -> dict[str, Any]:
    """Compile one profile into canonical profile.payload.json."""
    clean_key = profile_key.strip()

    if not clean_key:
        return failure_payload("", "profile_key is required.")

    profile_dir = resolve_profile_dir(clean_key)
    profile_dir.mkdir(parents=True, exist_ok=True)

    intake_path = profile_dir / "profile.intake.json"
    payload_path = profile_dir / "profile.payload.json"

    if payload_path.exists() and not force:
        return read_json(payload_path)

    if not intake_path.exists():
        return failure_payload(
            clean_key,
            f"Missing profile.intake.json: {intake_path}",
            profile_dir=profile_dir,
        )

    intake = read_json(intake_path)

    payload: dict[str, Any] = {
        "success": True,
        "version": CANONICAL_PROFILE_COMPILER_VERSION,
        "profile_key": clean_key,
        "profile_dir": str(profile_dir),
        "payload_path": str(payload_path),
        "identity": build_identity(clean_key, intake),
        "birth": build_birth(intake),
        "death": build_death(intake),
        "lifecycle": build_lifecycle(intake),
        "cipher": missing_layer("cipher", "Cipher compiler not wired into canonical compiler yet."),
        "kamea": missing_layer("kamea", "Kamea compiler not wired into canonical compiler yet."),
        "graph": missing_layer("graph", "Graph compiler not wired into canonical compiler yet."),
        "topology": missing_layer("topology", "Topology compiler not wired into canonical compiler yet."),
        "resonance": missing_layer("resonance", "Resonance compiler not wired into canonical compiler yet."),
        "fingerprint": missing_layer("fingerprint", "Fingerprint compiler not wired into canonical compiler yet."),
        "temporal": build_temporal(intake),
        "classification": {},
        "narrative": missing_layer("narrative", "Narrative compiler not wired into canonical compiler yet."),
        "evidence": [],
        "metrics": {},
        "diagnostics": {
            "warnings": [],
            "errors": [],
            "created_at": now_utc(),
            "compiler": "canonical_profile_compiler",
        },
    }

    payload["metrics"] = build_metrics(payload)
    payload["classification"] = classify_profile(payload)
    payload["metrics"] = build_metrics(payload)

    write_json(payload_path, payload)

    return payload


def build_identity(profile_key: str, intake: dict[str, Any]) -> dict[str, Any]:
    """Build canonical identity block."""
    identity = intake.get("identity", {}) if isinstance(intake.get("identity"), dict) else {}

    name = (
        identity.get("display_name")
        or identity.get("full_name")
        or intake.get("name")
        or intake.get("full_name")
        or profile_key.replace("_", " ").title()
    )

    return {
        "profile_key": profile_key,
        "name": name,
        "display_name": name,
        "full_name": identity.get("full_name") or name,
    }


def build_birth(intake: dict[str, Any]) -> dict[str, Any]:
    """Build canonical birth block."""
    birth = intake.get("birth", {}) if isinstance(intake.get("birth"), dict) else {}

    return {
        "date": birth.get("date") or intake.get("birth_date", ""),
        "time": birth.get("time") or intake.get("birth_time", ""),
        "place": birth.get("place") or intake.get("birth_place", "") or intake.get("birth_location", ""),
        "date_status": birth.get("date_status", "missing"),
        "time_status": birth.get("time_status", "missing"),
        "place_status": birth.get("place_status", "missing"),
    }


def build_death(intake: dict[str, Any]) -> dict[str, Any]:
    """Build canonical death block."""
    death = intake.get("death", {}) if isinstance(intake.get("death"), dict) else {}

    return {
        "date": death.get("date") or intake.get("death_date", ""),
        "place": death.get("place") or intake.get("death_place", ""),
        "date_status": death.get("date_status", "open_or_missing"),
        "place_status": death.get("place_status", "missing"),
        "lifecycle_status": death.get("lifecycle_status", "open_lifecycle"),
    }


def build_lifecycle(intake: dict[str, Any]) -> dict[str, Any]:
    """Build lifecycle block from intake."""
    return {
        "status": "compiled",
        "major_events": intake.get("major_events", []),
        "notes": intake.get("notes", ""),
    }


def build_temporal(intake: dict[str, Any]) -> dict[str, Any]:
    """Build canonical temporal block."""
    try:
        birth = build_birth(intake)
        identity = intake.get("identity", {}) if isinstance(intake.get("identity"), dict) else {}

        temporal_intake = {
            **intake,
            "name": identity.get("display_name") or identity.get("full_name") or intake.get("profile_key", ""),
            "birth_date": birth.get("date", ""),
            "birth_time": birth.get("time", ""),
            "birth_place": birth.get("place", ""),
            "birth_location": birth.get("place", ""),
        }

        birth_data = build_birth_data_from_intake(temporal_intake)
        natal_payload = build_natal_chart_payload(birth_data)

        return {
            "status": "compiled",
            "birth": birth,
            "natal": {
                "ephemeris": natal_payload.get("ephemeris", {}),
                "sidereal": natal_payload.get("sidereal", {}),
            },
            "summary": natal_payload.get("ephemeris", {}).get("summary", {}),
            "warnings": natal_payload.get("warnings", []),
            "errors": natal_payload.get("errors", []),
        }

    except Exception as exc:
        return {
            "status": "missing",
            "reason": f"Temporal compilation failed: {exc}",
            "required_inputs": ["birth.date", "birth.time", "birth.place"],
            "warnings": [],
            "errors": [str(exc)],
        }


def build_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    """Build canonical profile metrics."""
    temporal = payload.get("temporal", {})
    topology = payload.get("topology", {})
    resonance = payload.get("resonance", {})
    classification = payload.get("classification", {})

    return {
        "has_identity": bool(payload.get("identity", {}).get("name")),
        "has_birth_date": bool(payload.get("birth", {}).get("date")),
        "has_birth_time": bool(payload.get("birth", {}).get("time")),
        "has_birth_location": bool(payload.get("birth", {}).get("place")),
        "has_temporal": temporal.get("status") == "compiled",
        "has_natal": bool(temporal.get("natal")),
        "has_ephemeris": bool(temporal.get("natal", {}).get("ephemeris")),
        "has_graph": payload.get("graph", {}).get("status") == "compiled",
        "has_topology": topology.get("status") == "compiled",
        "has_resonance": resonance.get("status") == "compiled",
        "has_fingerprint": payload.get("fingerprint", {}).get("status") == "compiled",
        "has_classification": bool(classification.get("structural_role")),
    }


def missing_layer(layer: str, reason: str) -> dict[str, Any]:
    """Return a stable missing-layer object."""
    return {
        "status": "missing",
        "layer": layer,
        "reason": reason,
        "required_inputs": [],
        "warnings": [],
        "errors": [],
    }


def failure_payload(
    profile_key: str,
    error: str,
    *,
    profile_dir: Path | None = None,
) -> dict[str, Any]:
    """Return failure payload."""
    return {
        "success": False,
        "version": CANONICAL_PROFILE_COMPILER_VERSION,
        "profile_key": profile_key,
        "profile_dir": str(profile_dir) if profile_dir else "",
        "payload_path": "",
        "warnings": [],
        "errors": [error],
    }


def read_json(path: Path) -> dict[str, Any]:
    """Read JSON artifact."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON artifact."""
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def now_utc() -> str:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()
