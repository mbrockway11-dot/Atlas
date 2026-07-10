"""Run Atlas Alpha Engine Framework v1."""

from __future__ import annotations

from atlas.investment.alpha.engines import (
    run_alpha_engines,
)


def main() -> None:
    report = run_alpha_engines()

    print(report["success"])
    print(
        report.get(
            "summary",
            report.get("error"),
        )
    )

    print("Engines:")

    for engine in report.get("engines", []):
        print({
            "engine_id": engine.get("engine_id"),
            "family": engine.get("family"),
            "active": engine.get("active"),
            "signal_rows": engine.get(
                "signal_rows"
            ),
            "missing_features": engine.get(
                "missing_features"
            ),
        })

    print("Outputs:")

    for name, path in (
        report.get("outputs", {}) or {}
    ).items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
