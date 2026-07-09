
"""Execution batch utilities."""

from __future__ import annotations

from datetime import datetime, UTC
from uuid import uuid4


def new_execution_batch(mode: str = "paper") -> dict:
    batch_id = str(uuid4())
    return {
        "execution_batch_id": batch_id,
        "mode": mode,
        "created_at": datetime.now(UTC).isoformat(),
        "live_trading_enabled": False,
    }
