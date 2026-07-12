"""Update Atlas Research Evidence Accumulator v1."""

from __future__ import annotations

from atlas.investment.research_evidence_accumulator import (
    build_research_evidence_accumulator_report,
)


def main() -> None:
    report = (
        build_research_evidence_accumulator_report()
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
        "Recommendations:",
        report[
            "recommendation_counts"
        ],
    )

    print("Top recommendations:")

    for row in report.get(
        "top_recommendations",
        [],
    ):
        print({
            "program_id": row.get(
                "research_program_id"
            ),
            "current_status": row.get(
                "current_status"
            ),
            "best_variant": row.get(
                "best_variant_id"
            ),
            "evidence_score": row.get(
                "best_variant_evidence_score"
            ),
            "durability": row.get(
                "best_variant_durability"
            ),
            "recommendation": row.get(
                "recommendation"
            ),
            "transition_authorized": row.get(
                "program_transition_authorized"
            ),
        })

    print("Outputs:")

    for name, path in report[
        "outputs"
    ].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
