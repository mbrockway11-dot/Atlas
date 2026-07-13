"""Deterministic market-session evaluation for Atlas investment workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from atlas.investment.execution.instruments import (
    get_instrument,
    normalize_symbol,
)


NEW_YORK = ZoneInfo(
    "America/New_York"
)

SUPPORTED_SESSIONS = {
    "CONTINUOUS",
    "US_EQUITIES",
    "FUTURES",
    "ALWAYS",
}


@dataclass(frozen=True)
class SessionStatus:
    """Result of evaluating one market session at one instant."""

    session_name: str
    evaluated_at: str
    timezone: str
    local_time: str
    is_open: bool
    reason: str
    next_transition_at: str | None
    holiday_calendar_applied: bool
    approximate: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_market_session(
    session_name: str,
    *,
    now: datetime | None = None,
) -> SessionStatus:
    """Evaluate one canonical Atlas market-session name."""
    current = ensure_utc(
        now
        or datetime.now(UTC)
    )

    normalized = str(
        session_name
    ).strip().upper()

    if normalized not in SUPPORTED_SESSIONS:
        raise KeyError(
            "UNKNOWN_MARKET_SESSION:"
            + normalized
        )

    if normalized in {
        "CONTINUOUS",
        "ALWAYS",
    }:
        return SessionStatus(
            session_name=normalized,
            evaluated_at=current.isoformat(),
            timezone="UTC",
            local_time=current.isoformat(),
            is_open=True,
            reason=(
                "CONTINUOUS_SESSION"
                if normalized == "CONTINUOUS"
                else "ALWAYS_AVAILABLE"
            ),
            next_transition_at=None,
            holiday_calendar_applied=False,
            approximate=False,
        )

    if normalized == "US_EQUITIES":
        return evaluate_us_equities(
            current
        )

    return evaluate_futures(
        current
    )


def evaluate_instrument_session(
    symbol: str,
    *,
    now: datetime | None = None,
) -> SessionStatus:
    """Evaluate the registry-defined market session for an instrument."""
    canonical = normalize_symbol(
        symbol
    )

    instrument = get_instrument(
        canonical
    )

    if instrument is None:
        raise KeyError(
            "UNREGISTERED_INSTRUMENT:"
            + canonical
        )

    return evaluate_market_session(
        instrument.market_session,
        now=now,
    )


def evaluate_symbol_sessions(
    symbols,
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    """Evaluate session eligibility for a collection of instruments."""
    canonical_symbols = sorted({
        normalize_symbol(symbol)
        for symbol in symbols
        if str(symbol).strip()
        and normalize_symbol(symbol) != "CASH"
    })

    rows = []

    for symbol in canonical_symbols:
        status = evaluate_instrument_session(
            symbol,
            now=now,
        )

        rows.append({
            "symbol": symbol,
            **status.to_dict(),
        })

    open_symbols = [
        row["symbol"]
        for row in rows
        if row["is_open"]
    ]

    closed_symbols = [
        row["symbol"]
        for row in rows
        if not row["is_open"]
    ]

    return {
        "all_open": bool(rows)
        and not closed_symbols,
        "any_open": bool(open_symbols),
        "open_symbols": open_symbols,
        "closed_symbols": closed_symbols,
        "counts": {
            "requested": len(rows),
            "open": len(open_symbols),
            "closed": len(closed_symbols),
        },
        "rows": rows,
    }


def evaluate_us_equities(
    current: datetime,
) -> SessionStatus:
    """Evaluate regular US-equity weekday trading hours."""
    local = current.astimezone(
        NEW_YORK
    )

    session_start = time(
        9,
        30,
    )

    session_end = time(
        16,
        0,
    )

    local_clock = local.time().replace(
        tzinfo=None
    )

    weekday = local.weekday()

    is_open = bool(
        weekday < 5
        and session_start
        <= local_clock
        < session_end
    )

    if weekday >= 5:
        reason = "WEEKEND"
    elif local_clock < session_start:
        reason = "BEFORE_SESSION"
    elif local_clock >= session_end:
        reason = "AFTER_SESSION"
    else:
        reason = "SESSION_OPEN"

    transition = next_weekday_transition(
        local=local,
        session_start=session_start,
        session_end=session_end,
        is_open=is_open,
    )

    return SessionStatus(
        session_name="US_EQUITIES",
        evaluated_at=current.isoformat(),
        timezone="America/New_York",
        local_time=local.isoformat(),
        is_open=is_open,
        reason=reason,
        next_transition_at=(
            transition
            .astimezone(UTC)
            .isoformat()
        ),
        holiday_calendar_applied=False,
        approximate=True,
    )


def evaluate_futures(
    current: datetime,
) -> SessionStatus:
    """Evaluate a conservative generic US futures session."""
    local = current.astimezone(
        NEW_YORK
    )

    weekday = local.weekday()

    local_clock = local.time().replace(
        tzinfo=None
    )

    maintenance_start = time(
        17,
        0,
    )

    reopen_time = time(
        18,
        0,
    )

    if weekday == 5:
        is_open = False
        reason = "SATURDAY_CLOSED"

    elif weekday == 6:
        is_open = local_clock >= reopen_time

        reason = (
            "SESSION_OPEN"
            if is_open
            else "SUNDAY_BEFORE_OPEN"
        )

    elif weekday == 4:
        is_open = local_clock < maintenance_start

        reason = (
            "SESSION_OPEN"
            if is_open
            else "WEEKEND_CLOSED"
        )

    else:
        is_open = not (
            maintenance_start
            <= local_clock
            < reopen_time
        )

        reason = (
            "SESSION_OPEN"
            if is_open
            else "DAILY_MAINTENANCE"
        )

    transition = next_futures_transition(
        local
    )

    return SessionStatus(
        session_name="FUTURES",
        evaluated_at=current.isoformat(),
        timezone="America/New_York",
        local_time=local.isoformat(),
        is_open=is_open,
        reason=reason,
        next_transition_at=(
            transition
            .astimezone(UTC)
            .isoformat()
        ),
        holiday_calendar_applied=False,
        approximate=True,
    )


def next_weekday_transition(
    *,
    local: datetime,
    session_start: time,
    session_end: time,
    is_open: bool,
) -> datetime:
    if is_open:
        return datetime.combine(
            local.date(),
            session_end,
            tzinfo=NEW_YORK,
        )

    local_clock = local.time().replace(
        tzinfo=None
    )

    if (
        local.weekday() < 5
        and local_clock < session_start
    ):
        return datetime.combine(
            local.date(),
            session_start,
            tzinfo=NEW_YORK,
        )

    candidate = next_weekday(
        local.date()
    )

    return datetime.combine(
        candidate,
        session_start,
        tzinfo=NEW_YORK,
    )


def next_futures_transition(
    local: datetime,
) -> datetime:
    weekday = local.weekday()

    local_clock = local.time().replace(
        tzinfo=None
    )

    if weekday == 5:
        return datetime.combine(
            local.date()
            + timedelta(days=1),
            time(18, 0),
            tzinfo=NEW_YORK,
        )

    if weekday == 6:
        if local_clock < time(18, 0):
            return datetime.combine(
                local.date(),
                time(18, 0),
                tzinfo=NEW_YORK,
            )

        return datetime.combine(
            local.date()
            + timedelta(days=1),
            time(17, 0),
            tzinfo=NEW_YORK,
        )

    if weekday == 4:
        if local_clock < time(17, 0):
            return datetime.combine(
                local.date(),
                time(17, 0),
                tzinfo=NEW_YORK,
            )

        return datetime.combine(
            local.date()
            + timedelta(days=2),
            time(18, 0),
            tzinfo=NEW_YORK,
        )

    if (
        time(17, 0)
        <= local_clock
        < time(18, 0)
    ):
        return datetime.combine(
            local.date(),
            time(18, 0),
            tzinfo=NEW_YORK,
        )

    return datetime.combine(
        local.date(),
        time(17, 0),
        tzinfo=NEW_YORK,
    )


def next_weekday(
    value: date,
) -> date:
    candidate = (
        value
        + timedelta(days=1)
    )

    while candidate.weekday() >= 5:
        candidate += timedelta(
            days=1
        )

    return candidate


def ensure_utc(
    value: datetime,
) -> datetime:
    if value.tzinfo is None:
        value = value.replace(
            tzinfo=UTC
        )

    return value.astimezone(
        UTC
    )


__all__ = [
    "NEW_YORK",
    "SUPPORTED_SESSIONS",
    "SessionStatus",
    "evaluate_instrument_session",
    "evaluate_market_session",
    "evaluate_symbol_sessions",
]
