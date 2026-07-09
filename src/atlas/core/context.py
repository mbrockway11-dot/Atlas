
"""Atlas Core runtime context."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import uuid4


@dataclass
class AtlasContext:
    mode: str = "paper"
    run_id: str = field(default_factory=lambda: str(uuid4()))
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    live_trading_enabled: bool = False
    metadata: dict = field(default_factory=dict)
