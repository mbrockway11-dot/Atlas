"""Run Research Hypothesis Validation Lab v1."""

from __future__ import annotations

from atlas.investment.hypothesis_validation import (
    build_hypothesis_validation_report,
)


def main() -> None:
    report = (
        build_hypothesis_validation_report()
    )

    print(report["success"])
    print(report["summary"])

    print(
        "Decision counts:",
        report.get(
            "decision_counts"
        ),
    )

    print("Leading results:")

    for row in report.get(
        "top_results",
        [],
    ):
        print({
            "hypothesis_id": row.get(
                "hypothesis_id"
            ),
            "decision": row.get(
                "decision"
            ),
            "engine_id": row.get(
                "engine_id"
            ),
            "feature": row.get(
                "feature"
            ),
            "state": row.get(
                "state"
            ),
            "score": row.get(
                "validation_score"
            ),
            "fold_win_rate": row.get(
                "fold_win_rate"
            ),
            "mean_advantage": row.get(
                "mean_return_advantage"
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
