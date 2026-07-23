"""Resumable Structural Codex compilation and profile-readiness auditing."""

from __future__ import annotations

import csv
from datetime import date, datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable

from atlas.library.profile_library import list_saved_profiles
from atlas.services.profile_path_service import PROJECT_ROOT, resolve_profile_dir
from atlas.services.structural_codex_service import (
    DEFAULT_POPULATION_PATH,
    build_structural_codex_for_profile,
)


REPORT_DIR = PROJECT_ROOT / "output" / "population" / "profile_readiness"
CHECKPOINT_PATH = REPORT_DIR / "bulk_codex_checkpoint.json"
JSON_REPORT_PATH = REPORT_DIR / "profile_readiness_report.json"
CSV_REPORT_PATH = REPORT_DIR / "profile_readiness_report.csv"
MARKDOWN_REPORT_PATH = REPORT_DIR / "profile_readiness_report.md"


def run_bulk_profile_codex(
    *,
    profile_keys: Iterable[str] | None = None,
    resume: bool = True,
    rebuild_existing: bool = False,
    checkpoint_every: int = 25,
) -> dict[str, Any]:
    """Compile Codices and persist a missing-data audit for every profile."""
    keys = sorted(dict.fromkeys(profile_keys or list_saved_profiles()))
    population_members = load_population_members(DEFAULT_POPULATION_PATH)
    checkpoint = read_json(CHECKPOINT_PATH) if resume else {}
    completed = set(checkpoint.get("completed_profile_keys", []))
    records_by_key = {
        row.get("profile_key"): row
        for row in checkpoint.get("records", [])
        if isinstance(row, dict) and row.get("profile_key")
    }
    failures = list(checkpoint.get("failures", []))

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    processed_this_run = 0
    for index, key in enumerate(keys, start=1):
        profile_dir = resolve_profile_dir(key)
        if key in completed and (profile_dir / "profile.readiness.json").exists():
            continue

        try:
            codex_path = profile_dir / "structural_codex.json"
            if rebuild_existing or not codex_path.exists():
                codex = build_structural_codex_for_profile(key, write_outputs=True)
            else:
                codex = read_json(codex_path)
            record = build_profile_readiness(
                key,
                codex=codex,
                population_members=population_members,
            )
            write_json(profile_dir / "profile.readiness.json", record)
            records_by_key[key] = record
            completed.add(key)
        except Exception as exc:  # pragma: no cover - batch boundary
            failures.append({
                "profile_key": key,
                "error": str(exc),
                "recorded_at": now_utc(),
            })

        processed_this_run += 1
        if processed_this_run % max(checkpoint_every, 1) == 0:
            persist_checkpoint(keys, completed, records_by_key, failures)
            print_progress(index, len(keys), records_by_key, failures)

    persist_checkpoint(keys, completed, records_by_key, failures)
    records = [records_by_key[key] for key in keys if key in records_by_key]
    report = build_readiness_report(keys, records, failures)
    write_readiness_reports(report)
    return report


def build_profile_readiness(
    profile_key: str,
    *,
    codex: dict[str, Any] | None = None,
    population_members: set[str] | None = None,
) -> dict[str, Any]:
    """Describe exactly which profile inputs and generated layers are missing."""
    profile_dir = resolve_profile_dir(profile_key)
    intake = read_json(profile_dir / "profile.intake.json")
    payload = read_json(profile_dir / "profile.payload.json")
    codex = codex or read_json(profile_dir / "structural_codex.json")

    identity = first_dict(payload.get("identity"), intake.get("identity"))
    birth = first_dict(payload.get("birth"), intake.get("birth"))
    name = first_value(
        identity.get("full_name"),
        identity.get("display_name"),
        identity.get("name"),
        intake.get("full_name"),
        intake.get("name"),
    )
    birth_date = first_value(birth.get("date"), intake.get("birth_date"))
    birth_time = first_value(birth.get("time"), intake.get("birth_time"))
    birth_place = first_value(
        birth.get("place"),
        intake.get("birth_place"),
        intake.get("birth_location"),
    )
    major_events = intake.get("major_events", [])
    source = intake.get("source") or intake.get("source_file")

    missing: list[dict[str, str]] = []
    add_gap(missing, not bool(name), "identity.full_name", "required", "Name-based numerology, Gematria, identity, and graph layers cannot be resolved.")
    add_gap(missing, not valid_iso_date(str(birth_date or "")), "birth.date", "required", "Life Path, birth cycles, and date-based temporal analysis remain unavailable.")
    add_gap(missing, not bool(birth_time), "birth.time", "recommended", "Time-sensitive natal and intraday temporal calculations remain unavailable or lower confidence.")
    add_gap(missing, not bool(birth_place), "birth.place", "recommended", "Location-sensitive temporal calculations remain unavailable or lower confidence.")
    add_gap(missing, not (profile_dir / "profile.payload.json").exists(), "profile.payload.json", "required", "Canonical structural layers have not been compiled.")
    add_gap(missing, not bool(codex.get("success")), "structural_codex.json", "required", "The evidence-linked Structural Codex could not be generated.")
    add_gap(missing, not (profile_dir / "profile.acf.json").exists(), "profile.acf.json", "optional", "Legacy Profile Observatory/ACF views may not be available; canonical Codex compilation is unaffected.")
    add_gap(missing, not bool(major_events), "major_events", "recommended", "Longitudinal validation and lifecycle interpretation have no event observations.")
    add_gap(missing, not bool(source), "source", "recommended", "Biographical inputs lack an explicit provenance citation.")
    if population_members is not None:
        add_gap(missing, profile_key not in population_members, "population_v2", "derived", "Profile is not represented in the current Population Intelligence v2 snapshot.")

    symbolic = codex.get("symbolic_profile", {}) if isinstance(codex, dict) else {}
    numerology = symbolic.get("numerology", {}) if isinstance(symbolic, dict) else {}
    gematria = symbolic.get("gematria", {}) if isinstance(symbolic, dict) else {}
    add_gap(missing, not bool(numerology.get("available")), "numerology", "derived", "Numerology could not be calculated from the available identity/birth inputs.")
    add_gap(missing, not bool(gematria.get("available")), "gematria", "derived", "Gematria could not be calculated from the available name.")

    required_missing = sum(row["severity"] == "required" for row in missing)
    enrichment_missing = sum(row["severity"] in {"recommended", "derived"} for row in missing)
    optional_missing = sum(row["severity"] == "optional" for row in missing)
    if required_missing:
        status = "incomplete"
    elif enrichment_missing or optional_missing:
        status = "core_complete_with_gaps"
    else:
        status = "complete"

    return {
        "schema_version": "atlas.profile-readiness.v1",
        "generated_at": now_utc(),
        "profile_key": profile_key,
        "name": name or profile_key.replace("_", " ").title(),
        "profile_dir": str(profile_dir),
        "status": status,
        "core_complete": required_missing == 0,
        "enrichment_complete": required_missing == 0 and enrichment_missing == 0,
        "missing_counts": {
            "required": required_missing,
            "recommended": sum(row["severity"] == "recommended" for row in missing),
            "derived": sum(row["severity"] == "derived" for row in missing),
            "optional": optional_missing,
            "total": len(missing),
        },
        "missing_data": missing,
        "availability": {
            "identity_name": bool(name),
            "birth_date": valid_iso_date(str(birth_date or "")),
            "birth_time": bool(birth_time),
            "birth_place": bool(birth_place),
            "canonical_payload": (profile_dir / "profile.payload.json").exists(),
            "structural_codex": bool(codex.get("success")),
            "numerology": bool(numerology.get("available")),
            "gematria": bool(gematria.get("available")),
            "acf_legacy": (profile_dir / "profile.acf.json").exists(),
            "major_events": bool(major_events),
            "source": bool(source),
            "population_v2": profile_key in (population_members or set()),
        },
        "notes": [row["impact"] for row in missing],
        "codex_errors": [str(item) for item in codex.get("errors", [])],
        "codex_warnings": [str(item) for item in codex.get("warnings", [])],
    }


def build_readiness_report(
    requested_keys: list[str],
    records: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    gap_counts: dict[str, int] = {}
    for record in records:
        status = str(record.get("status"))
        status_counts[status] = status_counts.get(status, 0) + 1
        for gap in record.get("missing_data", []):
            field = str(gap.get("field"))
            gap_counts[field] = gap_counts.get(field, 0) + 1
    return {
        "schema_version": "atlas.profile-readiness-report.v1",
        "generated_at": now_utc(),
        "requested_profile_count": len(requested_keys),
        "audited_profile_count": len(records),
        "failed_profile_count": len(failures),
        "status_counts": dict(sorted(status_counts.items())),
        "missing_field_counts": dict(sorted(gap_counts.items(), key=lambda item: (-item[1], item[0]))),
        "records": records,
        "failures": failures,
        "outputs": {
            "json": str(JSON_REPORT_PATH),
            "csv": str(CSV_REPORT_PATH),
            "markdown": str(MARKDOWN_REPORT_PATH),
            "checkpoint": str(CHECKPOINT_PATH),
        },
    }


def write_readiness_reports(report: dict[str, Any]) -> None:
    write_json(JSON_REPORT_PATH, report)
    rows = []
    for record in report.get("records", []):
        availability = record.get("availability", {})
        rows.append({
            "profile_key": record.get("profile_key"),
            "name": record.get("name"),
            "status": record.get("status"),
            "core_complete": record.get("core_complete"),
            "enrichment_complete": record.get("enrichment_complete"),
            "missing_required": record.get("missing_counts", {}).get("required", 0),
            "missing_total": record.get("missing_counts", {}).get("total", 0),
            "missing_fields": "|".join(gap.get("field", "") for gap in record.get("missing_data", [])),
            **{f"has_{key}": value for key, value in availability.items()},
        })
    CSV_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else ["profile_key", "name", "status"]
    with CSV_REPORT_PATH.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Atlas Profile Readiness Report",
        "",
        f"- Requested profiles: **{report.get('requested_profile_count', 0)}**",
        f"- Audited profiles: **{report.get('audited_profile_count', 0)}**",
        f"- Failed profiles: **{report.get('failed_profile_count', 0)}**",
        "",
        "## Status Counts",
        "",
    ]
    lines.extend(f"- {key}: **{value}**" for key, value in report.get("status_counts", {}).items())
    lines.extend(["", "## Most Common Missing Data", ""])
    lines.extend(f"- `{key}`: **{value}**" for key, value in report.get("missing_field_counts", {}).items())
    MARKDOWN_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def persist_checkpoint(
    requested_keys: list[str],
    completed: set[str],
    records_by_key: dict[str, dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    write_json(CHECKPOINT_PATH, {
        "schema_version": "atlas.bulk-codex-checkpoint.v1",
        "updated_at": now_utc(),
        "requested_profile_count": len(requested_keys),
        "completed_profile_keys": sorted(completed),
        "records": [records_by_key[key] for key in sorted(records_by_key)],
        "failures": failures,
    })


def print_progress(index: int, total: int, records: dict[str, Any], failures: list[Any]) -> None:
    print(f"progress={index}/{total} audited={len(records)} failures={len(failures)}", flush=True)


def load_population_members(path: Path) -> set[str]:
    payload = read_json(path)
    return {
        str(row.get("profile_key"))
        for row in payload.get("profiles", [])
        if isinstance(row, dict) and row.get("profile_key")
    }


def add_gap(target: list[dict[str, str]], condition: bool, field: str, severity: str, impact: str) -> None:
    if condition:
        target.append({"field": field, "severity": severity, "impact": impact})


def first_dict(*values: Any) -> dict[str, Any]:
    return next((value for value in values if isinstance(value, dict) and value), {})


def first_value(*values: Any) -> Any:
    return next((value for value in values if value not in (None, "", [])), "")


def valid_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except (TypeError, ValueError):
        return False


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
