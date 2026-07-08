
"""Broker interface schema."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class BrokerOrder:
    asset: str
    side: str
    action: str
    weight: float
    broker: str = "paper"
    status: str = "CREATED"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
