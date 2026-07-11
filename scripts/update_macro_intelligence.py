"""Run Macro Intelligence v1."""

from __future__ import annotations

from atlas.investment.macro_intelligence import (
    build_macro_intelligence_report,
)


def main() -> None:
    report = (
        build_macro_intelligence_report()
    )

    print(report["success"])
    print(report["summary"])
    print(
        "Macro environment:",
        report.get(
            "macro_environment"
        ),
    )
    print(
        "Counts:",
        report.get("counts"),
    )

    print("Outputs:")

    for name, path in report.get(
        "outputs",
        {},
    ).items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
