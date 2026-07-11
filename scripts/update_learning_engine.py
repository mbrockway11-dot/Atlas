"""Run Learning Engine v3.1."""

from __future__ import annotations

from atlas.investment.learning import (
    build_learning_report,
)


def main() -> None:
    report = build_learning_report()

    print(report["success"])
    print(report["summary"])

    print("Counts:")
    print(report.get("counts"))

    print("Engine recommendations:")

    for row in report.get(
        "engine_recommendations",
        [],
    ):
        print({
            "engine_id": row.get(
                "engine_id"
            ),
            "decision": row.get(
                "latest_decision"
            ),
            "reliability": row.get(
                "reliability"
            ),
            "recommendation": row.get(
                "recommendation"
            ),
            "multiplier": row.get(
                "learning_weight_multiplier"
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
