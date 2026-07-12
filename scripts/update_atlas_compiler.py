"""Run Atlas Compiler v1."""

from __future__ import annotations

from atlas.investment.atlas_compiler import (
    build_atlas_compiler_report,
)


def main() -> None:
    report = (
        build_atlas_compiler_report()
    )

    print(report["success"])
    print(report["summary"])

    print(
        "State hash:",
        report.get(
            "state_hash"
        ),
    )

    print(
        "Counts:",
        report.get(
            "counts"
        ),
    )

    print(
        "Validation:",
        report.get(
            "validation"
        ),
    )

    print("Outputs:")

    for name, path in report.get(
        "outputs",
        {},
    ).items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
