"""Service boundary for Kamea consciousness-flow and riverbed comparison."""

from __future__ import annotations

import json
from typing import Any

from atlas.kamea_flow.confluence import build_riverbed_confluence
from atlas.kamea_flow.report import build_kamea_flow_report
from atlas.library.profile_library import list_saved_profiles
from atlas.services.profile_path_service import profile_artifact_path
from atlas.visualization.kamea_riverbed import render_planetary_riverbed_svg
from atlas.visualization.kamea_unified_shape import render_unified_kamea_shape_svg


def list_kamea_flow_profiles() -> list[str]:
    return [key for key in list_saved_profiles() if profile_artifact_path(key, "profile.payload.json").exists()]


def build_kamea_consciousness_flow_payload(profile_a: str, profile_b: str | None = None) -> dict[str, Any]:
    try:
        report_a = _build_profile_report(profile_a)
        report_b = _build_profile_report(profile_b) if profile_b else None
        confluence = build_riverbed_confluence(profile_a, report_a, profile_b, report_b) if profile_b and report_b else None
        return {
            "success": True,
            "version": "atlas.kamea-consciousness-flow.v1",
            "profile_a": profile_a,
            "profile_b": profile_b,
            "reports": {"profile_a": report_a, "profile_b": report_b},
            "confluence": confluence,
            "warnings": [
                "Consciousness flow is a symbolic model, not an empirical consciousness measurement.",
                "Results depend on the recorded identity name, cipher rules, and projection version.",
            ],
            "errors": [],
        }
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "version": "atlas.kamea-consciousness-flow.v1", "profile_a": profile_a, "profile_b": profile_b, "reports": {}, "confluence": None, "warnings": [], "errors": [str(exc)]}


def render_riverbed_for_profile(report: dict[str, Any], planet: str) -> str:
    row = next((item for item in report.get("riverbed", {}).get("planetary_riverbeds", []) if item.get("planet") == planet), None)
    return render_planetary_riverbed_svg(row) if row else ""


def render_unified_shape_for_profile(report: dict[str, Any], profile_key: str) -> str:
    return render_unified_kamea_shape_svg(report.get("shape", {}), title=f"{profile_key.replace('_', ' ').title()} — Unified Kamea Shape")


def _build_profile_report(profile_key: str | None) -> dict[str, Any]:
    if not profile_key:
        raise ValueError("profile key is required")
    path = profile_artifact_path(profile_key, "profile.payload.json")
    if not path.exists():
        raise FileNotFoundError(f"Canonical profile payload not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return build_kamea_flow_report(payload)
