"""Research orchestrator command safety policy."""

from __future__ import annotations

import shlex
import sys
from pathlib import Path

from atlas.investment.research_scheduler.registry import (
    JOB_MAP,
)


DENIED_TOKENS = {
    "git",
    "gh",
    "curl",
    "wget",
    "ssh",
    "scp",
    "ftp",
    "powershell",
    "pwsh",
    "cmd",
    "bash",
    "sh",
}

DENIED_FRAGMENTS = {
    "broker",
    "live_execution",
    "place_order",
    "submit_order",
    "trade_execution",
    "production_deploy",
    "deploy_production",
}


def resolve_registered_command(
    job_id: str,
) -> list[str]:
    """Resolve one scheduler command into a safe argv list."""
    if job_id not in JOB_MAP:
        raise ValueError(
            f"Unregistered research job: {job_id}"
        )

    command = JOB_MAP[
        job_id
    ].command

    parts = shlex.split(
        command,
        posix=False,
    )

    if len(parts) < 2:
        raise ValueError(
            f"Malformed research command: {command}"
        )

    executable = parts[0].strip(
        '"'
    ).lower()

    if executable not in {
        "python",
        "python.exe",
    }:
        raise ValueError(
            "Only registered Python research commands "
            "may be executed."
        )

    script = Path(
        parts[1].strip('"')
    )

    if (
        script.is_absolute()
        or script.suffix.lower() != ".py"
        or not script.parts
        or script.parts[0] != "scripts"
    ):
        raise ValueError(
            "Research command must target a Python file "
            "inside scripts/."
        )

    normalized = " ".join(
        parts
    ).lower()

    for token in DENIED_TOKENS:
        if token in {
            part.strip('"').lower()
            for part in parts
        }:
            raise ValueError(
                f"Denied command token: {token}"
            )

    for fragment in DENIED_FRAGMENTS:
        if fragment in normalized:
            raise ValueError(
                "Potential execution or deployment command "
                f"was rejected: {fragment}"
            )

    expected = JOB_MAP[
        job_id
    ].command

    if command != expected:
        raise ValueError(
            "Scheduler command does not match the canonical "
            "job registry."
        )

    return [
        sys.executable,
        script.as_posix(),
        *[
            part.strip('"')
            for part in parts[2:]
        ],
    ]

