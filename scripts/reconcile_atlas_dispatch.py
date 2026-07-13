"""Reconcile the latest controlled Atlas dispatch."""

from __future__ import annotations

from atlas.investment.dispatch_reconciliation import (
    reconcile_dispatch,
)


def main() -> int:
    report = reconcile_dispatch()

    print(
        "ATLAS DISPATCH RECONCILIATION "
        + report["outcome"]
    )
    print(report["summary"])
    print(
        "Post-dispatch health:",
        report[
            "post_dispatch_health"
        ],
    )
    print(
        "Next remediation:",
        report[
            "next_remediation"
        ],
    )
    print("Outputs:")

    for name, path in report[
        "outputs"
    ].items():
        print(f"- {name}: {path}")

    return (
        1
        if report["outcome"]
        in {
            "FAILED",
            "SCOPE_VIOLATION",
        }
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
