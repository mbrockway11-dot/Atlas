"""Atomic single-instance lock for Atlas scheduler iterations."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path


class SchedulerLock:
    """Exclusive filesystem lock using atomic creation."""

    def __init__(
        self,
        path: Path,
    ) -> None:
        self.path = Path(
            path
        )

        self.acquired = False

    def acquire(self) -> None:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        flags = (
            os.O_CREAT
            | os.O_EXCL
            | os.O_WRONLY
        )

        try:
            descriptor = os.open(
                self.path,
                flags,
            )

        except FileExistsError as error:
            raise RuntimeError(
                "SCHEDULER_ALREADY_RUNNING:"
                + str(
                    self.path
                )
            ) from error

        payload = {
            "pid": os.getpid(),
            "acquired_at": (
                datetime.now(
                    UTC
                ).isoformat()
            ),
        }

        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                payload,
                handle,
                sort_keys=True,
            )

        self.acquired = True

    def release(self) -> None:
        if not self.acquired:
            return

        try:
            self.path.unlink(
                missing_ok=True
            )

        finally:
            self.acquired = False

    def __enter__(self):
        self.acquire()

        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        self.release()


__all__ = [
    "SchedulerLock",
]
