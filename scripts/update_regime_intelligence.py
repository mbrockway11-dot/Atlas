"""Run Regime Intelligence v1."""

from __future__ import annotations

from atlas.investment.regime_intelligence import (
    build_regime_intelligence_report,
)


def main() -> None:
    report = (
        build_regime_intelligence_report()
    )

    print(report["success"])
    print(report["summary"])

    regime = report.get(
        "regime",
        {},
    )

    print("Regime:")
    print({
        "regime": regime.get(
            "regime"
        ),
        "primary": regime.get(
            "primary_regime"
        ),
        "secondary": regime.get(
            "secondary_regime"
        ),
        "confidence": regime.get(
            "confidence"
        ),
        "transition": regime.get(
            "is_transition"
        ),
        "stability": regime.get(
            "stability_score"
        ),
    })

    print("Engine suitability:")

    for row in report.get(
        "engine_suitability",
        [],
    ):
        print({
            "engine_id": row.get(
                "engine_id"
            ),
            "family": row.get(
                "family"
            ),
            "effective_suitability": (
                row.get(
                    "effective_suitability"
                )
            ),
        })

    print("Outputs:")

    for name, path in report.get(
        "outputs",
        {},
    ).items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
