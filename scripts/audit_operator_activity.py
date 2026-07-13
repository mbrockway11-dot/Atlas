"""Audit Atlas operator-control activity and integrity chain."""

from __future__ import annotations

from atlas.investment.control_plane_operator_audit import (
    load_latest_operator_audit,
    read_operator_events,
    validate_operator_audit_chain,
)


def main() -> int:
    events = read_operator_events()
    latest = (
        load_latest_operator_audit()
    )

    validation = (
        validate_operator_audit_chain(
            events
        )
    )

    index_matches = bool(
        int(
            latest.get(
                "event_count",
                0,
            )
        )
        == len(events)
    )

    latest_hash_matches = bool(
        (
            not events
            and not latest.get(
                "latest_event_hash",
                "",
            )
        )
        or (
            events
            and str(
                latest.get(
                    "latest_event_hash",
                    "",
                )
            )
            == str(
                events[-1].get(
                    "event_hash",
                    "",
                )
            )
        )
    )

    success = bool(
        validation["valid"]
        and index_matches
        and latest_hash_matches
    )

    print(
        "ATLAS OPERATOR AUDIT "
        + (
            "PASSED"
            if success
            else "FAILED"
        )
    )
    print(
        "Events:",
        len(events),
    )
    print(
        "Operators:",
        len(
            latest.get(
                "operator_ids",
                [],
            )
            or []
        ),
    )
    print(
        "Sessions:",
        len(
            latest.get(
                "session_ids",
                [],
            )
            or []
        ),
    )
    print(
        "Chain valid:",
        validation["valid"],
    )
    print(
        "Latest index matches:",
        index_matches,
    )
    print(
        "Latest hash matches:",
        latest_hash_matches,
    )

    if validation["errors"]:
        print("Errors:")

        for error in validation[
            "errors"
        ]:
            print("-", error)

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
