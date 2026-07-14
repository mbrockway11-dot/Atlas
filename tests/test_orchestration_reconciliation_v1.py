from __future__ import annotations

from atlas.investment.orchestration.reconciliation import reconcile


def scheduler():
    return {
        "decision_id": "decision-1",
        "jobs": [
            {"job_id": "one", "script": "scripts/one.py", "depends_on": []},
            {
                "job_id": "two",
                "script": "scripts/two.py",
                "depends_on": ["one"],
            },
        ],
    }


def orchestration():
    return {
        "decision_id": "decision-1",
        "jobs": [
            {
                "job_id": "one",
                "script": "scripts/one.py",
                "depends_on": [],
                "status": "DRY_RUN",
            },
            {
                "job_id": "two",
                "script": "scripts/two.py",
                "depends_on": ["one"],
                "status": "DRY_RUN",
            },
        ],
        "safety": {
            "paper_only": True,
            "live_execution": False,
        },
    }


def test_matching_scheduler_and_orchestration_pass() -> None:
    report = reconcile(scheduler(), orchestration())
    assert report.status == "PASS"
    assert report.matched_job_count == 2
    assert report.missing_jobs == []
    assert report.paper_only is True
    assert report.live_execution is False


def test_missing_job_fails_reconciliation() -> None:
    actual = orchestration()
    actual["jobs"] = actual["jobs"][:1]

    report = reconcile(scheduler(), actual)

    assert report.status == "FAIL"
    assert report.missing_jobs == ["two"]
    assert any(issue["code"] == "MISSING_JOB" for issue in report.issues)


def test_out_of_order_job_is_detected() -> None:
    actual = orchestration()
    actual["jobs"] = list(reversed(actual["jobs"]))

    report = reconcile(scheduler(), actual)

    assert report.status == "FAIL"
    assert report.out_of_order_jobs == ["two"]


def test_live_execution_boundary_violation_fails() -> None:
    actual = orchestration()
    actual["safety"]["paper_only"] = False
    actual["safety"]["live_execution"] = True

    report = reconcile(scheduler(), actual)

    assert report.status == "FAIL"
    assert any(
        issue["code"] == "SAFETY_BOUNDARY_VIOLATION"
        for issue in report.issues
    )
