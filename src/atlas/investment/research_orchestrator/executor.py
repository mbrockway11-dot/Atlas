"""Safe research-job subprocess execution."""

from __future__ import annotations

import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from atlas.investment.research_orchestrator.config import (
    LOG_DIR,
)
from atlas.investment.research_orchestrator.safety import (
    resolve_registered_command,
)


def execute_job(
    *,
    job_id: str,
    run_id: str,
    timeout_seconds: int,
    root: Path,
) -> dict[str, Any]:
    """Execute one registered research job."""
    argv = resolve_registered_command(
        job_id
    )

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_job_id = job_id.replace(
        "/",
        "_",
    )

    stdout_path = (
        LOG_DIR
        / f"{run_id}__{safe_job_id}__stdout.log"
    )

    stderr_path = (
        LOG_DIR
        / f"{run_id}__{safe_job_id}__stderr.log"
    )

    started_at = datetime.now(
        UTC
    )

    started_counter = time.perf_counter()

    result = {
        "job_id": job_id,
        "status": "FAILED",
        "started_at": (
            started_at.isoformat()
        ),
        "completed_at": "",
        "duration_seconds": 0.0,
        "returncode": None,
        "stdout_path": str(
            stdout_path
        ),
        "stderr_path": str(
            stderr_path
        ),
        "error": "",
        "execution_authorized": True,
        "execution_instruction": False,
    }

    try:
        completed = subprocess.run(
            argv,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=max(
                1,
                int(timeout_seconds),
            ),
            check=False,
        )

        stdout_path.write_text(
            completed.stdout or "",
            encoding="utf-8",
        )

        stderr_path.write_text(
            completed.stderr or "",
            encoding="utf-8",
        )

        result["returncode"] = (
            completed.returncode
        )

        result["status"] = (
            "SUCCEEDED"
            if completed.returncode == 0
            else "FAILED"
        )

        if completed.returncode != 0:
            result["error"] = (
                "Research command returned "
                f"{completed.returncode}."
            )

    except subprocess.TimeoutExpired as error:
        result["status"] = "TIMED_OUT"

        result["error"] = (
            "Research command exceeded timeout."
        )

        stdout_value = (
            error.stdout.decode(
                "utf-8",
                errors="replace",
            )
            if isinstance(
                error.stdout,
                bytes,
            )
            else error.stdout
        )

        stderr_value = (
            error.stderr.decode(
                "utf-8",
                errors="replace",
            )
            if isinstance(
                error.stderr,
                bytes,
            )
            else error.stderr
        )

        stdout_path.write_text(
            stdout_value or "",
            encoding="utf-8",
        )

        stderr_path.write_text(
            stderr_value or "",
            encoding="utf-8",
        )

    except OSError as error:
        result["status"] = "FAILED"
        result["error"] = (
            f"{type(error).__name__}: {error}"
        )

    completed_at = datetime.now(
        UTC
    )

    result["completed_at"] = (
        completed_at.isoformat()
    )

    result["duration_seconds"] = round(
        time.perf_counter()
        - started_counter,
        8,
    )

    return result
