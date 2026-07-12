"""Run Variant Review Board v1."""

from __future__ import annotations

from atlas.investment.variant_review import (
    build_variant_review_report,
)


def main() -> None:
    report = (
        build_variant_review_report()
    )

    print(report["success"])
    print(report["summary"])

    print(
        "Decision counts:",
        report.get(
            "decision_counts"
        ),
    )

    print("Ranked variants:")

    for row in report.get(
        "top_variants",
        [],
    ):
        print({
            "rank": row.get(
                "review_rank"
            ),
            "variant_id": row.get(
                "variant_id"
            ),
            "variant_name": row.get(
                "variant_name"
            ),
            "score": row.get(
                "overall_review_score"
            ),
            "recommendation": row.get(
                "recommended_decision"
            ),
            "priority": row.get(
                "implementation_priority"
            ),
            "review_status": row.get(
                "review_status"
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
