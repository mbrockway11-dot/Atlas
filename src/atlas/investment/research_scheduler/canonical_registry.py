"""Canonical Atlas research job registry.

This module is the single source of truth for dependency ordering,
commands, output artifacts, priorities, and freshness policy.  The
scheduler and orchestrator consume these immutable specifications.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResearchJobSpec:
    """One schedulable Atlas research stage."""

    job_id