"""Tests for dependency-aware stabilization planning."""

from __future__ import annotations

from atlas.investment.research_orchestrator.safety import (
    resolve_registered_command,
)
from atlas.investment.research_orchestrator.stabilization import (
    build_stabilization_commands,
)
from atlas.investment.research_scheduler import topological_order


def test_stabilization_commands_follow_canonical_dag_exactly():
    job_ids = topological_order()
    commands = build_stabilization_commands()

    assert len(commands) == len(job_ids)
    assert commands == [
        resolve_registered_command(job_id)
        for job_id in job_ids
    ]


def test_stabilization_commands_are_registered_python_scripts():
    for command in build_stabilization_commands():
        assert len(command) >= 2
        assert command[1].startswith("scripts/")
        assert command[1].endswith(".py")
