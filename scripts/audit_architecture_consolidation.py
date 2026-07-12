"""Command-line wrapper for the Atlas architecture consolidation audit."""

from __future__ import annotations

from atlas.investment.architecture_audit import format_summary, run_audit


def main() -> int:
    errors = run_audit()
    if errors:
        print("ATLAS ARCHITECTURE CONSOLIDATION AUDIT FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    artifact_count, job_count, loader_count = format_summary()
    print("ATLAS ARCHITECTURE CONSOLIDATION AUDIT PASSED")
    print(f"Registered artifacts: {artifact_count}")
    print(f"Registered jobs: {job_count}")
    print(f"Audited loaders: {loader_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
