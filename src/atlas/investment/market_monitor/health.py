"""Venue freshness and health evaluation for Atlas G.23."""

from __future__ import annotations

from datetime import datetime, timezone

from .contracts import VenueHealth, VenueHealthState, VenueTicker


def parse_timestamp(value: str) -> datetime:
    if value.isdigit():
        numeric = int(value)
        seconds = numeric / 1000 if numeric > 10_000_000_000 else numeric
        return datetime.fromtimestamp(seconds, tz=timezone.utc)

    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def evaluate_venue_health(
    ticker: VenueTicker,
    *,
    now: datetime | None = None,
    degraded_after_seconds: float = 5.0,
    stale_after_seconds: float = 15.0,
) -> VenueHealth:
    current = now or datetime.now(timezone.utc)
    received = parse_timestamp(ticker.received_at)
    age = max(0.0, (current - received).total_seconds())

    if age > stale_after_seconds:
        state = VenueHealthState.STALE
        message = "Ticker exceeded stale threshold"
    elif age > degraded_after_seconds:
        state = VenueHealthState.DEGRADED
        message = "Ticker freshness is degraded"
    else:
        state = VenueHealthState.HEALTHY
        message = "Ticker is current"

    return VenueHealth(
        venue=ticker.venue,
        state=state,
        checked_at=current.isoformat(),
        message=message,
        stale_age_seconds=age,
        paper_only=True,
        live_execution=False,
        credentials_used=False,
    )


__all__ = ["evaluate_venue_health", "parse_timestamp"]
