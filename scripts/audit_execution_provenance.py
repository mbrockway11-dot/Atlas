"""Audit Atlas execution provenance history."""

from __future__ import annotations

from collections import Counter

from atlas.investment.research_orchestrator.provenance import (
    load_latest_provenance,
    read_provenance_events,
)


def main() -> int:
    events = read_provenance_events()
    latest = load_latest_provenance()

    duplicate_ids = [
        event_id
        for event_id, count
        in Counter(
            str(
                event.get(
                    "event_id",
                    "",
                )
            )
            for event in events
        ).items()
        if event_id and count > 1
    ]

    malformed = [
        index
        for index, event
        in enumerate(
            events,
            start=1,
        )
        if not all(
            key in event
            for key in (
                "event_id",
                "run_id",
                "job_id",
                "status",
                "command_signature",
                "build_identity_hash",
                "required_input_manifest",
                "required_output_manifest",
            )
        )
    ]

    success = bool(
        not duplicate_ids
        and not malformed
        and int(
            latest.get(
                "event_count",
                0,
            )
        )
        == len(events)
    )

    print(
        "ATLAS EXECUTION PROVENANCE AUDIT "
        + (
            "PASSED"
            if success
            else "FAILED"
        )
    )
    print("Events:", len(events))
    print(
        "Latest indexed jobs:",
        len(
            latest.get(
                "jobs",
                {},
            )
        ),
    )
    print(
        "Duplicate event IDs:",
        len(duplicate_ids),
    )
    print(
        "Malformed events:",
        len(malformed),
    )
    print(
        "Status counts:",
        latest.get(
            "status_counts",
            {},
        ),
    )

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
