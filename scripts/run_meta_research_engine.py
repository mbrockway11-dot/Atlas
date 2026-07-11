"""Run Meta Research Engine v1."""

from __future__ import annotations

from atlas.investment.meta_research import (
    build_meta_research_report,
)


def main() -> None:
    report = build_meta_research_report()

    print(report["success"])
    print(report["summary"])
    print(
        "Counts:",
        report.get("counts"),
    )

    print("Top research priorities:")

    for row in report.get(
        "top_priorities",
        [],
    ):
        print({
            "rank": row.get(
                "research_rank"
            ),
            "target": row.get(
                "research_target"
            ),
            "type": row.get(
                "target_type"
            ),
            "priority": row.get(
                "priority_score"
            ),
            "confidence": row.get(
                "confidence"
            ),
        })

    print("Top hypotheses:")

    for row in report.get(
        "top_hypotheses",
        [],
    ):
        print({
            "hypothesis_id": row.get(
                "hypothesis_id"
            ),
            "type": row.get(
                "hypothesis_type"
            ),
            "engine": row.get(
                "engine_id"
            ),
            "family": row.get(
                "family"
            ),
            "feature": row.get(
                "feature"
            ),
            "state": row.get(
                "state"
            ),
            "priority": row.get(
                "priority"
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
