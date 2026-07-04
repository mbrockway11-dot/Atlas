"""Profile compile service.

Compiles an intake-created Atlas profile into generated profile artifacts.

This service is intentionally defensive:
- It tries the canonical Atlas compiler first.
- It writes a minimal fallback ACF if the compiler is unavailable.
- It reports exactly what was created and what still needs attention.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from atlas.services.lifecycle_intelligence_service import build_lifecycle_record


PROFILE_COMPILE_SERVICE_VERSION = "1.0"

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LIBRARY_DIR = PROJECT_ROOT / "output" / "library"


def compile_person_profile(
    profile_key: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Compile a profile from profile.intake.json into Atlas artifacts."""
    clean_key = profile_key.strip()

    if not clean_key:
        return failure_payload("profile_key is required.")

    profile_dir = LIBRARY_DIR / clean_key
    intake_path = profile_dir / "profile.intake.json"

    if not intake_path.exists():
        return failure_payload(f"Missing intake file: {intake_path}")

    intake = read_json(intake_path)

    created_files: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []

    compiler_result = try_canonical_compile(clean_key)

    if compiler_result.get("success") and (profile_dir / "profile.acf.json").exists():
        created_files.extend(existing_artifacts(profile_dir))
        warnings.extend(compiler_result.get("warnings", []))
    else:
        if compiler_result.get("success"):
            warnings.append(
                "Canonical compiler reported success but did not create profile.acf.json; writing fallback artifacts."
            )
        else:
            warnings.append("Canonical compiler was unavailable or failed; writing fallback artifacts.")

        warnings.extend(compiler_result.get("warnings", []))
        errors.extend(compiler_result.get("errors", []))

        fallback = write_fallback_artifacts(
            profile_dir=profile_dir,
            intake=intake,
            force=force,
        )
        created_files.extend(fallback.get("created_files", []))
        warnings.extend(fallback.get("warnings", []))

    return {
        "success": bool((profile_dir / "profile.acf.json").exists()),
        "version": PROFILE_COMPILE_SERVICE_VERSION,
        "profile_key": clean_key,
        "profile_dir": str(profile_dir),
        "created_files": sorted(set(created_files)),
        "warnings": dedupe(warnings),
        "errors": dedupe(errors),
        "artifact_status": artifact_status(profile_dir),
        "compiler_result": compiler_result,
    }


def try_canonical_compile(profile_key: str) -> dict[str, Any]:
    """Try to use the canonical Atlas compiler if available."""
    try:
        from atlas.core.compiler import compile_profile_payload  # type: ignore

        payload = compile_profile_payload(profile_key)

        if isinstance(payload, dict):
            return {
                "success": bool(payload.get("success")),
                "warnings": [str(item) for item in payload.get("warnings", [])],
                "errors": [str(item) for item in payload.get("errors", [])],
                "payload_keys": list(payload.keys()),
            }

        return {
            "success": False,
            "warnings": ["compile_profile_payload returned a non-dict payload."],
            "errors": [],
            "payload_keys": [],
        }

    except Exception as exc:  # pragma: no cover - defensive integration boundary
        return {
            "success": False,
            "warnings": [],
            "errors": [f"Canonical compile failed: {exc}"],
            "payload_keys": [],
        }


def write_fallback_artifacts(
    *,
    profile_dir: Path,
    intake: dict[str, Any],
    force: bool,
) -> dict[str, Any]:
    """Write minimal artifacts so the profile can appear in Atlas."""
    created_files: list[str] = []
    warnings: list[str] = []

    profile_key = intake.get("profile_key") or intake.get("identity", {}).get("profile_key")
    identity = intake.get("identity", {})
    birth = intake.get("birth", {})

    acf_path = profile_dir / "profile.acf.json"
    summary_path = profile_dir / "profile_summary.json"
    interpretation_path = profile_dir / "profile_interpretation.json"
    report_path = profile_dir / "codex_report.md"
    lifecycle_path = profile_dir / "lifecycle.json"

    if force or not acf_path.exists():
        acf = {
            "success": True,
            "version": PROFILE_COMPILE_SERVICE_VERSION,
            "profile_key": profile_key,
            "identity": identity,
            "birth": birth,
            "data": {
                "canonical_structural_signature": {
                    "identity": identity,
                    "temporal": {
                        "birth": birth,
                        "temporal_status": "intake_only",
                    },
                    "topology": {
                        "status": "pending_full_compile",
                    },
                }
            },
            "metrics": {
                "has_identity": bool(identity.get("full_name")),
                "has_birth_date": bool(birth.get("date")),
                "has_birth_time": bool(birth.get("time")),
                "has_birth_location": bool(birth.get("place")),
                "has_temporal": bool(birth.get("date")),
                "has_topology": False,
                "fallback_compile": True,
            },
            "warnings": [
                "Fallback ACF generated. Run canonical compiler for full deterministic layers."
            ],
            "created_at": now_iso(),
        }
        write_json(acf_path, acf)
        created_files.append(str(acf_path))

    if force or not summary_path.exists():
        summary = {
            "success": True,
            "version": PROFILE_COMPILE_SERVICE_VERSION,
            "profile_key": profile_key,
            "name": identity.get("display_name") or identity.get("full_name") or profile_key,
            "summary": "Profile created through intake. Full Atlas interpretation requires canonical compilation.",
            "birth": birth,
            "created_at": now_iso(),
        }
        write_json(summary_path, summary)
        created_files.append(str(summary_path))

    if force or not interpretation_path.exists():
        interpretation = {
            "success": True,
            "version": PROFILE_COMPILE_SERVICE_VERSION,
            "profile_key": profile_key,
            "interpretation": {
                "direct_answer": "This profile has intake data and is ready for full Atlas compilation.",
                "limitations": [
                    "Fallback interpretation only.",
                    "Run canonical compiler to generate graph, temporal, Kamea, and narrative layers.",
                ],
            },
            "created_at": now_iso(),
        }
        write_json(interpretation_path, interpretation)
        created_files.append(str(interpretation_path))

    if force or not report_path.exists():
        name = identity.get("display_name") or identity.get("full_name") or profile_key
        report = f"""# {name}

## Atlas Intake Report

This profile was created through the Profile Builder intake flow.

## Birth Data

- Date: {birth.get("date") or "missing"}
- Time: {birth.get("time") or "missing"}
- Place: {birth.get("place") or "missing"}

## Status

Fallback artifacts are present. Run the canonical Atlas compiler to generate the full deterministic profile.
"""
        report_path.write_text(report, encoding="utf-8")
        created_files.append(str(report_path))

    if force or not lifecycle_path.exists():
        death = intake.get("death", {})
        major_events = intake.get("major_events", [])

        lifecycle = build_lifecycle_record(
            profile_key=str(profile_key or ""),
            birth_date=str(birth.get("date", "")),
            birth_time=str(birth.get("time", "")),
            birth_place=str(birth.get("place", "")),
            death_date=str(death.get("date", "")),
            death_place=str(death.get("place", "")),
            major_events=major_events if isinstance(major_events, list) else [],
            notes=str(intake.get("notes", "")),
        )

        write_json(lifecycle_path, lifecycle)
        created_files.append(str(lifecycle_path))

    if not created_files:
        warnings.append("No fallback artifacts were written because files already exist. Use force=True to overwrite.")

    return {
        "created_files": created_files,
        "warnings": warnings,
    }


def artifact_status(profile_dir: Path) -> dict[str, bool]:
    """Return status for expected profile artifacts."""
    names = [
        "profile.intake.json",
        "profile.acf.json",
        "profile_summary.json",
        "profile_interpretation.json",
        "codex_report.md",
        "lifecycle.json",
        "research_session.json",
    ]

    return {
        name: (profile_dir / name).exists()
        for name in names
    }


def existing_artifacts(profile_dir: Path) -> list[str]:
    """Return existing known artifacts."""
    return [
        str(profile_dir / name)
        for name, exists in artifact_status(profile_dir).items()
        if exists
    ]


def read_json(path: Path) -> dict[str, Any]:
    """Read JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON file."""
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def now_iso() -> str:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def dedupe(values: list[str]) -> list[str]:
    """Deduplicate while preserving order."""
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)

    return result


def failure_payload(error: str) -> dict[str, Any]:
    """Build failure payload."""
    return {
        "success": False,
        "version": PROFILE_COMPILE_SERVICE_VERSION,
        "profile_key": "",
        "profile_dir": "",
        "created_files": [],
        "warnings": [],
        "errors": [error],
        "artifact_status": {},
        "compiler_result": {},
    }
