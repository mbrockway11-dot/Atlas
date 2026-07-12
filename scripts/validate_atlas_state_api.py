"""Validate Atlas State API v1."""

from __future__ import annotations

from atlas.investment.state_api import (
    build_state_api_validation_report,
    list_components,
    list_sections,
)


def main() -> None:
    report = (
        build_state_api_validation_report()
    )

    print(report["success"])
    print(report["summary"])

    print(
        "State hash:",
        report[
            "validation"
        ][
            "state_hash"
        ],
    )

    print(
        "Sections:",
        list_sections(),
    )

    print(
        "Components:",
        list_components(),
    )

    print("Outputs:")

    for name, path in report.get(
        "outputs",
        {},
    ).items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
