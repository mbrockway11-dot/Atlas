"""Regression tests for Atlas Architecture Consolidation v1."""

from __future__ import annotations

from atlas.investment.research_orchestrator.safety import (
    resolve_registered_command,
)
from atlas.investment.research_scheduler import (
    JOB_MAP,
    JOBS,
    topological_order,
)


def test_canonical_registry_has_unique_job_ids():
    job_ids = [job.job_id for job in JOBS]

    assert len(job_ids) == len(set(job_ids))