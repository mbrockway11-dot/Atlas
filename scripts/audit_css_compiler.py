"""Audit Atlas Canonical Structural Signature compiler."""

from __future__ import annotations

import time
import traceback
from typing import Any

from atlas.core.compiler import compile_profile
from atlas.library.profile_library import list_saved_profiles


LIMIT = 10


def main() -> None:
    """Run CSS compiler audit."""
    print()
    print("ATLAS CSS COMPILER AUDIT")
    print("=" * 80)

    profiles = list_saved_profiles()

    selected = profiles[:LIMIT]
    results = []

    started = time.perf_counter()

    for index, profile_key in enumerate(selected, start=1):
        print(f"[{index}/{len(selected)}] {profile_key}")

        result = audit_profile(profile_key)
        results.append(result)

        status = "PASS" if result["success"] else "FAIL"
        print(f"  {status}")

        for warning in result["warnings"]:
            print(f"  warning: {warning}")

        for error in result["errors"]:
            print(f"  error: {error}")

    elapsed = time.perf_counter() - started

    summary = build_summary(results, elapsed)

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for key, value in summary.items():
        print(f"{key}: {value}")

    failures = [item for item in results if not item["success"]]

    if failures:
        print()
        print("FAILED PROFILES")
        print("=" * 80)

        for failure in failures:
            print(f"- {failure['profile_key']}")
            for error in failure["errors"]:
                print(f"  {error}")

        raise SystemExit(1)

    print()
    print("CSS COMPILER AUDIT PASSED")
    raise SystemExit(0)


def audit_profile(profile_key: str) -> dict[str, Any]:
    """Audit one compiled CSS profile."""
    started = time.perf_counter()

    errors: list[str] = []
    warnings: list[str] = []

    try:
        css = compile_profile(profile_key)
    except Exception as exc:  # noqa: BLE001
        return {
            "profile_key": profile_key,
            "success": False,
            "errors": [str(exc)],
            "warnings": [],
            "elapsed_seconds": round(time.perf_counter() - started, 4),
            "traceback": traceback.format_exc(),
        }

    if css.identity is None:
        errors.append("missing identity layer")
    else:
        if not css.identity.profile_key:
            errors.append("missing identity.profile_key")

        if not css.identity.canonical_name:
            errors.append("missing identity.canonical_name")

        if not css.identity.birth_date:
            warnings.append("missing identity.birth_date")

        if not css.identity.birth_time:
            warnings.append("missing identity.birth_time")

        if not css.identity.birth_location:
            warnings.append("missing identity.birth_location")

    if not has_cipher(css):
        warnings.append("cipher layer empty")

    if not has_kamea(css):
        warnings.append("kamea layer empty")

    if not has_temporal(css):
        warnings.append("temporal layer empty")

    if not css.metadata.get("compiler_version"):
        errors.append("missing compiler metadata")

    return {
        "profile_key": profile_key,
        "success": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "elapsed_seconds": round(time.perf_counter() - started, 4),
        "has_identity": css.identity is not None,
        "has_cipher": has_cipher(css),
        "has_kamea": has_kamea(css),
        "has_temporal": has_temporal(css),
        "has_birth_date": bool(css.identity and css.identity.birth_date),
        "has_birth_time": bool(css.identity and css.identity.birth_time),
        "has_birth_location": bool(css.identity and css.identity.birth_location),
    }


def build_summary(results: list[dict[str, Any]], elapsed: float) -> dict[str, Any]:
    """Build audit summary."""
    total = len(results)
    passed = sum(1 for item in results if item["success"])
    failed = total - passed

    return {
        "profiles_tested": total,
        "passed": passed,
        "failed": failed,
        "identity_complete": sum(1 for item in results if item["has_identity"]),
        "cipher_present": sum(1 for item in results if item["has_cipher"]),
        "kamea_present": sum(1 for item in results if item["has_kamea"]),
        "temporal_present": sum(1 for item in results if item["has_temporal"]),
        "birth_date_present": sum(1 for item in results if item["has_birth_date"]),
        "birth_time_present": sum(1 for item in results if item["has_birth_time"]),
        "birth_location_present": sum(
            1 for item in results if item["has_birth_location"]
        ),
        "warning_count": sum(len(item["warnings"]) for item in results),
        "error_count": sum(len(item["errors"]) for item in results),
        "elapsed_seconds": round(elapsed, 4),
        "average_seconds": round(elapsed / total, 4) if total else 0.0,
    }


def has_cipher(css: Any) -> bool:
    """Return whether CSS has cipher data."""
    return any(
        [
            bool(css.cipher.ordinal),
            bool(css.cipher.hebrew_phonetic),
            bool(css.cipher.hebrew_transliteration),
            bool(css.cipher.gematria),
        ]
    )


def has_kamea(css: Any) -> bool:
    """Return whether CSS has Kamea data."""
    return any(
        [
            bool(css.kamea.topology),
            bool(css.kamea.planetary_graphs),
            bool(css.kamea.resonance),
            bool(css.kamea.graph_metrics),
            bool(css.kamea.fingerprint),
        ]
    )


def has_temporal(css: Any) -> bool:
    """Return whether CSS has temporal data."""
    return any(
        [
            bool(css.temporal.natal),
            bool(css.temporal.transits),
            bool(css.temporal.dasha),
            bool(css.temporal.calibration),
        ]
    )


if __name__ == "__main__":
    main()