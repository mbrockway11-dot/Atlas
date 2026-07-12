"""Update Atlas Research Candidate Consolidator v1."""

from __future__ import annotations

from atlas.investment.research_candidate_consolidator import (
    build_candidate_consolidator_report,
)


def main() -> None:
    report = (
        build_candidate_consolidator_report()
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
        "Reduction ratio:",
        report["reduction_ratio"],
    )

    print("Top programs:")

    for program in report.get(
        "top_programs",
        [],
    ):
        print({
            "rank": program.get(
                "program_rank"
            ),
            "program_id": program.get(
                "research_program_id"
            ),
            "title": program.get(
                "program_title"
            ),
            "engine": program.get(
                "parent_engine_id"
            ),
            "members": program.get(
                "member_count"
            ),
            "score": program.get(
                "program_priority_score"
            ),
            "confidence": program.get(
                "cluster_confidence"
            ),
            "recommendation": program.get(
                "recommendation"
            ),
            "execution_authorized": (
                program.get(
                    "execution_authorized"
                )
            ),
        })

    print("Outputs:")

    for name, path in report[
        "outputs"
    ].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
