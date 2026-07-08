
"""Shared Sigil V32 adapter schema."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class StrategySignal:
    source: str
    engine: str
    asset: str | None
    timestamp: str | None
    signal_state: str | None
    action: str | None
    direction: str | None
    target_exposure: float
    entry_ready: bool
    setup_active: bool
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
