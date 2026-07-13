"""Controlled process runner for approved Atlas orchestration commands."""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence


@dataclass(frozen=True)
class ProcessResult:
    """Normalized subprocess result."""

    return_code: int
    stdout: str
    stderr: str
    elapsed_ms: float


class ProcessRunner(
    Protocol
):
    """Injectable process execution boundary."""

    def run(
        self,
        command: Sequence[str],
        *,
        timeout_seconds: int,
        cwd: Path,
    ) -> ProcessResult:
        ...


class SafeSubprocessRunner:
    """Run approved commands without a shell."""

    def run(
        self,
        command: Sequence[str],
        *,
        timeout_seconds: int,
        cwd: Path,
    ) -> ProcessResult:
        normalized = list(
            command
        )

        if not normalized:
            raise ValueError(
                "PROCESS_COMMAND_EMPTY"
            )

        if normalized[0].lower() in {
            "python",
            "python.exe",
        }:
            normalized[0] = (
                sys.executable
            )

        started = (
            time.perf_counter()
        )

        try:
            completed = subprocess.run(
                normalized,
                cwd=str(
                    cwd
                ),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=int(
                    timeout_seconds
                ),
                check=False,
                shell=False,
            )

        except subprocess.TimeoutExpired as error:
            elapsed_ms = (
                time.perf_counter()
                - started
            ) * 1_000.0

            raise RuntimeError(
                "PROCESS_TIMEOUT:"
                + str(
                    timeout_seconds
                )
            ) from error

        elapsed_ms = (
            time.perf_counter()
            - started
        ) * 1_000.0

        return ProcessResult(
            return_code=int(
                completed.returncode
            ),
            stdout=str(
                completed.stdout
                or ""
            ),
            stderr=str(
                completed.stderr
                or ""
            ),
            elapsed_ms=(
                elapsed_ms
            ),
        )


__all__ = [
    "ProcessResult",
    "ProcessRunner",
    "SafeSubprocessRunner",
]
