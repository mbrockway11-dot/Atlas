"""Deterministic market-session calendar for Atlas scheduling."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from atlas.investment.execution.instruments import get_instrument, normalize_symbol

NEW_YORK = ZoneInfo("America/New_York")
SESSION_CALENDAR_VERSION = "1.0.0"


@dataclass(frozen=True)
class SessionState:
    session: str
    is_open: bool
    reason: str
    evaluated_at: str
    local_time: str
    next_open_at: str | None
    next_close_at: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_market_session(session: str, *, now: datetime | None = None) -> SessionState:
    current = ensure_aware(now or datetime.now(UTC))
    normalized = str(session).strip().upper()

    if normalized in {"ALWAYS", "CONTINUOUS"}:
        return SessionState(
            session