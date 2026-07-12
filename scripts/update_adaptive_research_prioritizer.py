"""Update Adaptive Research Prioritizer v1."""

from __future__ import annotations

from atlas.investment.adaptive_research_prioritizer import (
    build_adaptive_research_prioritizer_report,
)


def main() -> None:
    report = (
        build_adaptive_research_prioritizer_report()
    )

    print(report["success"])
    print(report["summary"])
    print(
        "State hash:",
        report["state_hash"],
    )
    print(
        "Counts:",
        report["counts"],
    )

    print("Top priorities:")

    for row in report.get(
        "top_priorities",
        [],
    ):
        print({
            "rank": row.get(
                "priority_rank"
            ),
            "candidate_id": row.get(
                "candidate_id"
            ),
            "title": row.get(
                "title"
            ),
            "score": row.get(
                "final_priority_score"
            ),
            "priority": row.get(
                "priority_band"
            ),
            "recommendation": row.get(
                "recommendation"
            ),
            "execution_authorized": row.get(
                "execution_authorized"
            ),
        })

    print("Outputs:")

    for name, path in report[
        "outputs"
    ].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
