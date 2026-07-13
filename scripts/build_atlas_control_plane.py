"""Build the unified Atlas Control Plane health snapshot."""

from __future__ import annotations

from atlas.investment.control_plane import (
    build_and_write_system_health,
)


def main() -> int:
    report = (
        build_and_write_system_health()
    )

    print(
        "ATLAS CONTROL PLANE "
        + report["overall_status"]
    )
    print(report["summary"])
    print("Counts:", report["counts"])
    print("Outputs:")

    for name, path in report[
        "outputs"
    ].items():
        print(f"- {name}: {path}")

    # Degraded operational state remains a valid snapshot.
    # Only structural/integrity-critical state returns failure.
    return (
        1
        if report["overall_status"]
        == "CRITICAL"
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
