"""Canonical multi-venue market-monitor contracts for Atlas G.23."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

SCHEMA_VERSION = "g23.market_monitor.v1"


class Venue(str, Enum):
    COINBASE = "COINBASE"
    KRAKEN = "KRAKEN"
    BINANCE = "BINANCE"


class VenueHealthState(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class VenueTicker:
    venue: Venue
    symbol: str
    bid: float
    ask: float
    bid_quantity: float
    ask_quantity: float
    last: float
    volume_24h: float
    timestamp: str
    received_at: str
    sequence: int | None = None
    paper_only: bool = True
    live_execution: bool = False
    credentials_used: bool = False


@dataclass(frozen=True)
class VenueHealth:
    venue: Venue
    state: VenueHealthState
    checked_at: str
    message: str
    stale_age_seconds: float
    paper_only: bool = True
    live_execution: bool = False
    credentials_used: bool = False


@dataclass(frozen=True)
class ConsolidatedTicker:
    symbol: str
    best_bid: float
    best_bid_venue: Venue
    best_ask: float
    best_ask_venue: Venue
    midpoint: float
    spread: float
    spread_bps: float
    last_median: float
    venue_count: int
    cross_venue_divergence_bps: float
    total_bid_quantity: float
    total_ask_quantity: float
    generated_at: str
    paper_only: bool = True
    live_execution: bool = False
    credentials_used: bool = False


__all__ = [
    "SCHEMA_VERSION",
    "ConsolidatedTicker",
    "Venue",
    "VenueHealth",
    "VenueHealthState",
    "VenueTicker",
]
