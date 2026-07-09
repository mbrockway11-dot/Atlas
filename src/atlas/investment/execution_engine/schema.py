
"""Execution Engine v3 schemas."""

from __future__ import annotations

from datetime import datetime, UTC
from uuid import uuid4


def new_batch(mode: str = "paper") -> dict:
    return {
        "execution_batch_id": str(uuid4()),
        "mode": mode,
        "created_at": datetime.now(UTC).isoformat(),
        "live_trading_enabled": False,
    }


def stable_order_key(asset: str, action: str, side: str, weight: float) -> str:
    return f"{asset}:{side}:{action}:{float(weight):.6f}"
