"""Run Atlas Research Scheduler v1."""

from __future__ import annotations

from atlas.investment.research_scheduler import (
    build_research_scheduler_report,
)


def main() -> None:
    report = (
        build_research_scheduler_report()
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

    print("Next jobs:")

    for job in report.get(
        "next_jobs",
        [],
    ):
        print({
            "rank": job.get(
                "schedule_rank"
            ),
            "job_id": job.get(
                "job_id"
            ),
            "priority": job.get(
                "priority"
            ),
            "status": job.get(
                "status"
            ),
            "reason": job.get(
                "reason"
            ),
            "command": job.get(
                "command"
            ),
            "execution_authorized": job.get(
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
