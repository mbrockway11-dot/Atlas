"""Canonical stabilization command planning.

Stabilization consumes the same registered jobs, dependency order, and command
safety policy as the continuous research orchestrator.  This module deliberately
contains no execution logic; it only exposes the deterministic command plan used
by the compatibility stabilization script.
"""

from __future__ import annotations

from atlas.investment.research_orchestrator.safety import (
    resolve_registered_command,
)
from atlas.investment.research_scheduler import topological_order


def build_stabilization_commands() -> list[list[str]]:
    """Return every registered research command in canonical DAG order."""
    return [
        resolve_registered_command(job_id)
        for job_id in topological_order()
    ]


__all__ = ["build_stabilization_commands"]
