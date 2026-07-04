"""Profile payload service.

Builds one canonical profile.payload.json from available Atlas artifacts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from atlas.services.temporal_composite_intelligence_service import build_temporal_composite_intelligence
from atlas.interpretation.profile_classifier import classify_profile


PROFILE_PAYLOAD_SERVICE_VERSION = "1.0"

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LIBRARY_DIR = PROJECT_ROOT / "output" / "library"
LEGACY_LIBRARY_DIR = PROJECT_ROOT / "data" / "profiles"


def build_profile_payload(profile_key: str) -> dict[str, Any]:
    """Build canonical profile payload from known artifacts."""
    clean_key = profile_key.strip()

    if not clean_key:
        return failure_payload("profile_key is required.")

    profile_dir = resolve_profile_dir(clean_key)

    if not profile_dir.exists():
        return failure_payload(f"Profile directory not found for: {clean_key}")

    intake = read_optional_json(profile_dir / "profile.intake.json")
    acf = read_optional_json(profile_dir / "profile.acf.json")
    summary = read_optional_json(profile_dir / "profile_summary.json")
    interpretation = read_optional_json(profile_dir / "profile_interpretation.json")
    lifecycle = read_optional_json(profile_dir / "lifecycle.json")

    payload = {
        "success": True,
        "version": PROFILE_PAYLOAD_SERVICE_VERSION,
        "profile_key": clean_key,
        "profile_dir": str(profile_dir),
        "identity": extract_identity(intake, acf, summary),
        "birth": extract_birth(intake, acf),
        "death": intake.get("death", {}),
        "major_events": intake.get("major_events", []),
        "lifecycle": lifecycle,
        "acf": acf,
        "summary": summary,
        "interpretation": interpretation,
        "graph": extract_graph(acf),
        "temporal": extract_temporal(acf, lifecycle, interpretation, clean_key),
        "morphology": extract_morphology(acf),
        "evidence": extract_evidence(acf, interpretation),
        "metrics": extract_metrics(acf),
        "artifact_status": artifact_status(profile_dir),
        "warnings": collect_warnings(intake, acf, lifecycle),
        "errors": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    classification = classify_profile(payload)
    payload["classification"] = classification

    interpretation_payload = payload.get("interpretation", {})
    if isinstance(interpretation_payload, dict):
        semantic = interpretation_payload.setdefault("semantic", {})
        semantic.update({
            "name": classification.get("name", ""),
            "structural_role": classification.get("structural_role", ""),
            "civilization_function": classification.get("civilization_function", ""),
            "cognitive_style": classification.get("cognitive_style", ""),
            "motivation": classification.get("motivation", ""),
            "emotional_pattern": classification.get("emotional_pattern", ""),
            "stress_response": classification.get("stress_response", ""),
            "growth_path": classification.get("growth_path", ""),
        })

    payload_path = profile_dir / "profile.payload.json"
    write_json(payload_path, payload)

    payload["payload_path"] = str(payload_path)

    return payload


def resolve_profile_dir(profile_key: str) -> Path:
    """Resolve profile directory across canonical and legacy libraries."""
    candidates = [
        LIBRARY_DIR / profile_key,
        LIBRARY_DIR / "profiles" / profile_key,
        PROJECT_ROOT / "output" / "console" / "individual" / profile_key,
        LEGACY_LIBRARY_DIR / profile_key,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def extract_identity(
    intake: dict[str, Any],
    acf: dict[str, Any],
    summary: dict[str, Any],
) -> dict[str, Any]:
    """Extract identity block."""
    identity = intake.get("identity") or acf.get("identity") or {}

    name = (
        identity.get("display_name")
        or identity.get("full_name")
        or summary.get("name")
        or intake.get("profile_key")
        or acf.get("profile_key")
        or ""
    )

    return {
        "profile_key": identity.get("profile_key") or intake.get("profile_key") or acf.get("profile_key", ""),
        "full_name": identity.get("full_name") or name,
        "display_name": identity.get("display_name") or name,
    }


def extract_birth(
    intake: dict[str, Any],
    acf: dict[str, Any],
) -> dict[str, Any]:
    """Extract birth block."""
    birth = intake.get("birth") or acf.get("birth") or {}

    return {
        "date": birth.get("date", ""),
        "time": birth.get("time", ""),
        "place": birth.get("place", ""),
        "date_status": birth.get("date_status", "unknown"),
        "time_status": birth.get("time_status", "unknown"),
        "place_status": birth.get("place_status", "unknown"),
    }


def extract_graph(acf: dict[str, Any]) -> dict[str, Any]:
    """Extract graph/topology area from ACF."""
    data = acf.get("data", {})
    signature = data.get("canonical_structural_signature", {})

    return {
        "topology": signature.get("topology", {}),
        "graph": signature.get("graph", {}),
        "graph_intelligence": data.get("graph_intelligence", {}),
    }


def extract_temporal(
    acf: dict[str, Any],
    lifecycle: dict[str, Any],
    interpretation: dict[str, Any],
    profile_key_fallback: str = "",
) -> dict[str, Any]:
    """Extract temporal area and attach temporal composite."""
    data = acf.get("data", {})
    signature = data.get("canonical_structural_signature", {})
    runtime = signature.get("temporal", {})
    semantic = interpretation.get("semantic", {}) if isinstance(interpretation, dict) else {}

    profile_key = (
        acf.get("profile_key")
        or data.get("profile_key")
        or semantic.get("profile_key")
        or profile_key_fallback
        or ""
    )

    graph_payload = {
        "summary": (
            data.get("graph_intelligence", {}).get("summary", "")
            or signature.get("topology", {}).get("summary", "")
        )
    }

    temporal_payloads = {
        profile_key: runtime
    } if profile_key else {}

    natal_payloads = {
        profile_key: runtime.get("natal", {})
    } if profile_key and isinstance(runtime, dict) else {}

    composite = build_temporal_composite_intelligence(
        profiles=[profile_key] if profile_key else [],
        date_window="current profile window",
        graph_payload=graph_payload,
        temporal_payloads=temporal_payloads,
        natal_payloads=natal_payloads,
        evidence=semantic.get("evidence", []),
    )

    return {
        "runtime": runtime,
        "lifecycle": lifecycle,
        "composite": composite,
        "temporal_composite_completed": bool(composite.get("success")),
        "summary": composite.get("human_summary", ""),
        "confidence": composite.get("confidence", "provisional"),
        "probable_outcomes": composite.get("probable_outcomes", []),
        "timing_cautions": composite.get("timing_cautions", []),
    }


def extract_morphology(acf: dict[str, Any]) -> dict[str, Any]:
    """Extract morphology area."""
    data = acf.get("data", {})
    signature = data.get("canonical_structural_signature", {})

    return {
        "identity_stack": signature.get("identity", {}),
        "morphology": signature.get("morphology", {}),
        "resonance": signature.get("resonance", {}),
    }


def extract_evidence(
    acf: dict[str, Any],
    interpretation: dict[str, Any],
) -> list[str]:
    """Extract evidence list."""
    evidence: list[str] = []

    for source in [
        acf.get("evidence", []),
        acf.get("data", {}).get("evidence", []),
        interpretation.get("evidence", []),
    ]:
        if isinstance(source, list):
            evidence.extend(str(item) for item in source)

    return dedupe(evidence)


def extract_metrics(acf: dict[str, Any]) -> dict[str, Any]:
    """Extract metrics."""
    metrics = acf.get("metrics", {})

    if not isinstance(metrics, dict):
        metrics = {}

    metrics["temporal_composite_completed"] = True
    return metrics


def collect_warnings(
    intake: dict[str, Any],
    acf: dict[str, Any],
    lifecycle: dict[str, Any],
) -> list[str]:
    """Collect warnings from component artifacts."""
    warnings: list[str] = []

    for source in [
        intake.get("warnings", []),
        acf.get("warnings", []),
        lifecycle.get("warnings", []),
    ]:
        if isinstance(source, list):
            warnings.extend(str(item) for item in source)

    return dedupe(warnings)


def artifact_status(profile_dir: Path) -> dict[str, bool]:
    """Return known artifact status."""
    names = [
        "profile.intake.json",
        "profile.acf.json",
        "profile_summary.json",
        "profile_interpretation.json",
        "lifecycle.json",
        "codex_report.md",
        "profile.payload.json",
    ]

    return {
        name: (profile_dir / name).exists()
        for name in names
    }


def read_optional_json(path: Path) -> dict[str, Any]:
    """Read JSON if present."""
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON artifact."""
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def dedupe(values: list[str]) -> list[str]:
    """Deduplicate strings preserving order."""
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
        "version": PROFILE_PAYLOAD_SERVICE_VERSION,
        "profile_key": "",
        "profile_dir": "",
        "payload_path": "",
        "warnings": [],
        "errors": [error],
    }
