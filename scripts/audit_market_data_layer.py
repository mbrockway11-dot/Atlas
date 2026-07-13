"""Audit the Atlas market-data abstraction layer."""

from __future__ import annotations

from atlas.investment.market_data import (
    load_market_snapshot,
    validate_market_data_audit,
)


def main() -> int:
    snapshot = (
        load_market_snapshot()
    )

    audit = (
        validate_market_data_audit()
    )

    contract = snapshot.get(
        "contract",
        {},
    )

    safe_contract = bool(
        not snapshot
        or (
            contract.get(
                "provider_neutral",
                False,
            )
            and contract.get(
                "broker_independent",
                False,
            )
            and not contract.get(
                "live_execution",
                False,
            )
            and not contract.get(
                "credentials_used",
                False,
            )
        )
    )

    snapshot_valid = bool(
        not snapshot
        or snapshot.get(
            "success",
            False,
        )
    )

    success = bool(
        audit["valid"]
        and safe_contract
        and snapshot_valid
    )

    print(
        "ATLAS MARKET DATA LAYER "
        + (
            "PASSED"
            if success
            else "FAILED"
        )
    )

    print(
        "Snapshot present:",
        bool(snapshot),
    )

    print(
        "Snapshot valid:",
        snapshot_valid,
    )

    print(
        "Provider neutral:",
        bool(
            not snapshot
            or contract.get(
                "provider_neutral",
                False,
            )
        ),
    )

    print(
        "Broker independent:",
        bool(
            not snapshot
            or contract.get(
                "broker_independent",
                False,
            )
        ),
    )

    print(
        "Credentials used:",
        bool(
            snapshot
            and contract.get(
                "credentials_used",
                False,
            )
        ),
    )

    print(
        "Audit chain valid:",
        audit["valid"],
    )

    print(
        "Audit events:",
        audit["event_count"],
    )

    if snapshot:
        print(
            "Snapshot ID:",
            snapshot.get(
                "snapshot_id",
                "",
            ),
        )

        print(
            "Counts:",
            snapshot.get(
                "counts",
                {},
            ),
        )

    if audit["errors"]:
        print("Audit errors:")

        for error in audit[
            "errors"
        ]:
            print("-", error)

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
