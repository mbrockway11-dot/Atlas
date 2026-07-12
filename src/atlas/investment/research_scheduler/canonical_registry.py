"""Canonical composed Atlas research job registry.

The mature legacy registry remains the compatibility source for established
jobs. This module composes it with research-program and evidence stages and
publishes one immutable registry for the scheduler and orchestrator.
"""

from __future__ import annotations

from atlas.investment.research_scheduler import registry as legacy_registry
from atlas.investment.research_scheduler.pipeline_jobs import compose_jobs


ResearchJobSpec = legacy_registry.ResearchJobSpec

JOBS = compose_jobs(
    legacy_registry.JOBS,
    ResearchJobSpec,
)

JOB_MAP = {
    job.job_id: job
    for job in JOBS
}


def install_canonical_registry() -> None:
    """Install the composed registry behind the legacy public interface."""
    legacy_registry.JOBS = JOBS
    legacy_registry.JOB_MAP = JOB_MAP


__all__ = [
    "JOB_MAP",
    "JOBS",
    "ResearchJobSpec",
    "install_canonical_registry",
]
