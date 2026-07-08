
"""Strategy Registry schema."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class RegisteredStrategySignal:
    source: str
    strategy_id: str
    strategy_family: str
    asset: str | None
    timestamp: str | None
    action: str | None
    direction: str | None
    confidence: float
    target_exposure: float
    rank: float | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
