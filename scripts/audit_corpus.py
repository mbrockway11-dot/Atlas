"""Audit Atlas corpus subsystem."""

from __future__ import annotations

import traceback


LIMIT = 3


def main() -> None:
    """Run corpus audit."""
    print()
    print("ATLAS CORPUS AUDIT")
    print("=" * 80)

    checks = [
        ("Profile Library", audit_profile_library),
        ("Corpus Research Runner", audit_corpus_research_runner),
        ("Population Intelligence", audit_population_intelligence),
    ]

    failures = []

    for label, fn in checks:
        try:
            result = fn()
            print_result(label, result)
            if not result.get("success"):
                failures.append((label, result))
        except Exception as exc:  # noqa: BLE001
            result = {
                "success": False,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
            failures.append((label, result))
            print_result(label, result)

    print()
    print("=" * 80)

    if failures:
        print(f"CORPUS AUDIT FAILED: {len(failures)} failure(s)")
        for label, result in failures:
            print(f"- {label}: {result.get('error') or result.get('errors')}")
        raise SystemExit(1)

    print("CORPUS AUDIT PASSED")
    raise SystemExit(0)


def audit_profile_library() -> dict:
    """Audit profile library."""
    from atlas.library.profile_library import list_saved_profiles

    profiles = list_saved_profiles()

    return {
        "success": len(profiles) > 0,
        "profile_count": len(profiles),
        "sample_profiles": profiles[:10],
    }


def audit_corpus_research_runner() -> dict:
    """Audit corpus research runner."""
    from atlas.corpus.research_runner import run_corpus_research

    payload = run_corpus_research(
        limit=LIMIT,
        include_memory=False,
        include_validation=True,
    )

    return {
        "success": payload.get("success") is True,
        "metrics": payload.get("metrics", {}),
        "errors": payload.get("errors", []),
        "warnings_count": len(payload.get("warnings", [])),
    }


def audit_population_intelligence() -> dict:
    """Audit population intelligence."""
    from atlas.research.population_intelligence import (
        build_population_intelligence_payload,
    )

    payload = build_population_intelligence_payload()

    return {
        "success": payload.get("success") is True,
        "metrics": payload.get("metrics", {}),
        "interpretation": (
            payload.get("data", {})
            .get("population_intelligence", {})
            .get("interpretation")
        ),
    }


def print_result(label: str, result: dict) -> None:
    """Print compact result."""
    status = "PASS" if result.get("success") else "FAIL"
    print()
    print(f"{label}: {status}")

    for key, value in result.items():
        if key == "success":
            continue
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()