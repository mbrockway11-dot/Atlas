"""Build the read-only Atlas remediation plan."""

from __future__ import annotations

from atlas.investment.control_plane import (
    build_and_write_system_health,
)
from atlas.investment.control_plane_remediation import (
    build_and_write_remediation_plan,
)


def main() -> int:
    health = (
        build_and_write_system_health()
    )

    plan = (
        build_and_write_remediation_plan(
            health
        )
    )

    print(
        "ATLAS REMEDIATION PLAN "
        + plan["plan_status"]
    )
    print(plan["summary"])
    print("Counts:", plan["counts"])
    print(
        "Execution:",
        plan["execution"],
    )
    print("Outputs:")

    for name, path in plan[
        "outputs"
    ].items():
        print(f"- {name}: {path}")

    # A blocked structural plan is a failure.
    # READY, MANUAL_REVIEW, and NO_ACTION are valid outputs.
    return (
        1
        if plan["plan_status"]
        == "BLOCKED"
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
