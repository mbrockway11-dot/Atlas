"""Update Atlas Research Program Manager v1."""

from __future__ import annotations

from atlas.investment.research_program_manager import (
    build_research_program_manager_report,
)


def main() -> None:
    report = (
        build_research_program_manager_report()
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
    print(
        "Statuses:",
        report["status_counts"],
    )

    print("Approval queue:")

    for row in report.get(
        "top_approval_queue",
        [],
    ):
        print({
            "program_id": row.get(
                "research_program_id"
            ),
            "title": row.get(
                "program_title"
            ),
            "engine": row.get(
                "parent_engine_id"
            ),
            "score": row.get(
                "program_priority_score"
            ),
            "confidence": row.get(
                "cluster_confidence"
            ),
            "blocked": row.get(
                "is_blocked"
            ),
        })

    print("Outputs:")

    for name, path in report[
        "outputs"
    ].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
