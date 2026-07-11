"""Run Atlas Alpha Research Lab v1."""

from __future__ import annotations

from atlas.investment.alpha.research_lab import (
    build_alpha_research_lab_report,
)


def main() -> None:
    report = build_alpha_research_lab_report(
        transaction_cost_bps=10.0,
    )

    print(report["success"])

    print(
        report.get(
            "summary",
            report.get("error"),
        )
    )

    print("Decision counts:")

    print(
        report.get(
            "decision_counts",
            {},
        )
    )

    print("Decisions:")

    for row in report.get(
        "decisions",
        [],
    ):
        print({
            "engine_id": row.get(
                "engine_id"
            ),
            "decision": row.get(
                "decision"
            ),
            "promotion_score": row.get(
                "promotion_score"
            ),
            "profit_factor": row.get(
                "profit_factor"
            ),
            "mean_return": row.get(
                "mean_return"
            ),
            "max_drawdown": row.get(
                "max_drawdown"
            ),
            "independence": row.get(
                "average_independence"
            ),
            "hard_failures": row.get(
                "hard_failures"
            ),
        })

    print("Outputs:")

    for name, path in (
        report.get(
            "outputs",
            {},
        )
    ).items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
