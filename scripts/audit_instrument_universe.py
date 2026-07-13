"""Audit the canonical Atlas multi-asset instrument universe."""

from __future__ import annotations

from atlas.investment.execution.instruments import (
    build_instrument_universe_report,
)


def main() -> int:
    report = (
        build_instrument_universe_report()
    )

    print(
        "ATLAS INSTRUMENT UNIVERSE "
        + (
            "PASSED"
            if report["success"]
            else "FAILED"
        )
    )

    print(
        "Registered:",
        report["counts"][
            "registered"
        ],
    )

    print(
        "Paper enabled:",
        report["counts"][
            "paper_enabled"
        ],
    )

    print(
        "Research only:",
        report["counts"][
            "paper_disabled"
        ],
    )

    print(
        "Asset classes:",
        report["counts"][
            "asset_classes"
        ],
    )

    print(
        "Aliases:",
        report["counts"][
            "aliases"
        ],
    )

    print(
        "Direct futures enabled:",
        report["contract"][
            "direct_futures_enabled"
        ],
    )

    if report["errors"]:
        print("Errors:")

        for error in report[
            "errors"
        ]:
            print("-", error)

    print(
        "Output:",
        report["output"],
    )

    return (
        0
        if report["success"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
