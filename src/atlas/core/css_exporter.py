"""Canonical Structural Signature exporter.

Compiles Atlas profile-library entries into stable CSS JSON artifacts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from atlas.core.compiler import compile_profile, compile_profile_payload
from atlas.library.profile_library import list_saved_profiles


CSS_EXPORTER_VERSION = "1.0"

DEFAULT_OUTPUT_DIR = Path("output") / "css"
CSS_INDEX_FILENAME = "css_index.json"


def export_css_library(
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    profile_keys: list[str] | None = None,
) -> dict[str, Any]:
    """Compile and export CSS JSON for all selected profiles."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    selected = profile_keys if profile_keys is not None else list_saved_profiles()

    results: list[dict[str, Any]] = []

    for index, profile_key in enumerate(selected, start=1):
        print(f"[{index}/{len(selected)}] exporting {profile_key}")

        result = export_css_profile(
            profile_key=profile_key,
            output_dir=out_dir,
        )
        results.append(result)

        status = "PASS" if result.get("success") else "FAIL"
        print(f"  {status}: {result.get('path')}")

    index_payload = build_css_index(results=results, output_dir=out_dir)
    index_path = out_dir / CSS_INDEX_FILENAME
    write_json(index_path, index_payload)

    return {
        "success": index_payload["failed_profiles"] == 0,
        "version": CSS_EXPORTER_VERSION,
        "errors": collect_errors(results),
        "warnings": collect_warnings(results),
        "data": {
            "css_index": index_payload,
        },
        "exports": {
            "css_index_path": str(index_path),
        },
        "metrics": {
            "profile_count": index_payload["profile_count"],
            "successful_profiles": index_payload["successful_profiles"],
            "failed_profiles": index_payload["failed_profiles"],
            "output_dir": str(out_dir),
            "index_path": str(index_path),
        },
    }


def export_css_profile(
    *,
    profile_key: str,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    """Compile and export one CSS profile."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        css = compile_profile(profile_key)
        payload = compile_profile_payload(profile_key)
        css_dict = css.to_dict()

        artifact = {
            "artifact_type": "canonical_structural_signature",
            "artifact_version": CSS_EXPORTER_VERSION,
            "exported_at": now_iso(),
            "profile_key": profile_key,
            "compiler_version": css.metadata.get("compiler_version"),
            "css": css_dict,
            "metrics": payload.get("metrics", {}),
        }

        path = css_path(output_dir=out_dir, profile_key=profile_key)
        write_json(path, artifact)

        return {
            "success": True,
            "profile_key": profile_key,
            "path": str(path),
            "compiler_version": css.metadata.get("compiler_version"),
            "metrics": payload.get("metrics", {}),
            "errors": [],
            "warnings": build_profile_warnings(payload.get("metrics", {})),
        }

    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "profile_key": profile_key,
            "path": str(css_path(output_dir=out_dir, profile_key=profile_key)),
            "errors": [str(exc)],
            "warnings": [],
        }


def build_css_index(
    *,
    results: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Any]:
    """Build CSS export index."""
    successful = [item for item in results if item.get("success")]
    failed = [item for item in results if not item.get("success")]

    return {
        "artifact_type": "css_export_index",
        "version": CSS_EXPORTER_VERSION,
        "generated_at": now_iso(),
        "output_dir": str(output_dir),
        "profile_count": len(results),
        "successful_profiles": len(successful),
        "failed_profiles": len(failed),
        "warning_count": sum(len(item.get("warnings", [])) for item in results),
        "error_count": sum(len(item.get("errors", [])) for item in results),
        "profiles": [
            {
                "profile_key": item.get("profile_key"),
                "success": item.get("success"),
                "path": item.get("path"),
                "compiler_version": item.get("compiler_version"),
                "metrics": item.get("metrics", {}),
                "warnings": item.get("warnings", []),
                "errors": item.get("errors", []),
            }
            for item in results
        ],
        "failed_profile_keys": [
            item.get("profile_key")
            for item in failed
        ],
    }


def build_profile_warnings(metrics: dict[str, Any]) -> list[str]:
    """Build non-fatal profile warnings from compiler metrics."""
    warnings: list[str] = []

    if not metrics.get("has_birth_date"):
        warnings.append("missing birth_date")

    if not metrics.get("has_birth_time"):
        warnings.append("missing birth_time")

    if not metrics.get("has_birth_location"):
        warnings.append("missing birth_location")

    if not metrics.get("has_cipher"):
        warnings.append("missing cipher")

    if not metrics.get("has_kamea"):
        warnings.append("missing kamea")

    if not metrics.get("has_temporal"):
        warnings.append("missing temporal")

    return warnings


def collect_errors(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collect export errors."""
    errors: list[dict[str, Any]] = []

    for result in results:
        for error in result.get("errors", []):
            errors.append(
                {
                    "profile_key": result.get("profile_key"),
                    "error": error,
                }
            )

    return errors


def collect_warnings(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collect export warnings."""
    warnings: list[dict[str, Any]] = []

    for result in results:
        for warning in result.get("warnings", []):
            warnings.append(
                {
                    "profile_key": result.get("profile_key"),
                    "warning": warning,
                }
            )

    return warnings


def css_path(*, output_dir: Path, profile_key: str) -> Path:
    """Return CSS artifact path."""
    return output_dir / f"{profile_key}.css.json"


def write_json(path: Path, data: dict[str, Any]) -> None:
    """Write JSON artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )


def now_iso() -> str:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def json_export(data: Any) -> str:
    """Serialize JSON."""
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)