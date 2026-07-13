"""Audit persistent Atlas paper-order lifecycle state."""

from __future__ import annotations

from atlas.investment.execution.lifecycle import (
    PaperOrderLifecycleStore,
)


def main() -> int:
    store = (
        PaperOrderLifecycleStore()
    )

    records = store.load_records()
    open_orders = (
        store.recover_open_orders()
    )
    validation = (
        store.validate_transition_chain()
    )

    state_errors = []

    for intent_id, record in (
        records.items()
    ):
        if (
            record.filled_quantity < 0
            or record.remaining_quantity < 0
        ):
            state_errors.append(
                "NEGATIVE_QUANTITY:"
                + intent_id
            )

        total = (
            record.filled_quantity
            + record.remaining_quantity
        )

        if (
            abs(
                total
                - record.requested_quantity
            )
            > 1e-9
        ):
            state_errors.append(
                "QUANTITY_MISMATCH:"
                + intent_id
            )

    success = bool(
        validation["valid"]
        and not state_errors
    )

    print(
        "ATLAS PAPER ORDER LIFECYCLE "
        + (
            "PASSED"
            if success
            else "FAILED"
        )
    )
    print(
        "Records:",
        len(records),
    )
    print(
        "Open orders:",
        len(open_orders),
    )
    print(
        "Transitions:",
        validation[
            "transition_count"
        ],
    )
    print(
        "Chain valid:",
        validation["valid"],
    )

    errors = (
        list(
            validation["errors"]
        )
        + state_errors
    )

    if errors:
        print("Errors:")

        for error in errors:
            print("-", error)

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
