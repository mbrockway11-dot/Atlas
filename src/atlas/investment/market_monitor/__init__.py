"""Atlas G.23 multi-venue market monitor."""

from .aggregation import consolidate_tickers
from .binance import build_binance_stream_names, parse_binance_book_ticker
from .coinbase import build_coinbase_subscription, parse_coinbase_ticker
from .collectors import (
    CoinbasePublicTickerCollector,
    CollectorConfig,
    CollectorMetrics,
    CollectorState,
    KrakenPublicTickerCollector,
    PublicWebSocketCollector,
)
from .contracts import (
    SCHEMA_VERSION,
    ConsolidatedTicker,
    Venue,
    VenueHealth,
    VenueHealthState,
    VenueTicker,
)
from .errors import (
    MarketDataStaleError,
    MarketDataValidationError,
    MarketMonitorError,
    VenueUnavailableError,
)
from .event_bridge import MarketEventBridge
from .health import evaluate_venue_health, parse_timestamp
from .kraken import build_kraken_subscription, parse_kraken_ticker
from .normalization import normalize_symbol, utc_now, validate_ticker
from .snapshot import (
    atomic_write_json,
    build_snapshot_payload,
    canonical_json,
    compute_hash,
)
from .supervisor import MarketMonitorSupervisor, SupervisorConfig

__all__ = [
    "SCHEMA_VERSION",
    "CoinbasePublicTickerCollector",
    "CollectorConfig",
    "CollectorMetrics",
    "CollectorState",
    "ConsolidatedTicker",
    "KrakenPublicTickerCollector",
    "MarketDataStaleError",
    "MarketDataValidationError",
    "MarketEventBridge",
    "MarketMonitorError",
    "MarketMonitorSupervisor",
    "PublicWebSocketCollector",
    "SupervisorConfig",
    "Venue",
    "VenueHealth",
    "VenueHealthState",
    "VenueTicker",
    "VenueUnavailableError",
    "atomic_write_json",
    "build_binance_stream_names",
    "build_coinbase_subscription",
    "build_kraken_subscription",
    "build_snapshot_payload",
    "canonical_json",
    "compute_hash",
    "consolidate_tickers",
    "evaluate_venue_health",
    "normalize_symbol",
    "parse_binance_book_ticker",
    "parse_coinbase_ticker",
    "parse_kraken_ticker",
    "parse_timestamp",
    "utc_now",
    "validate_ticker",
]
