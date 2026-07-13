"""Provider-neutral Atlas market-data abstraction layer."""

from atlas.investment.market_data.cache import (
    CacheStatistics,
    CachedMarketDataProvider,
)
from atlas.investment.market_data.coinbase import (
    COINBASE_BASE_URL,
    COINBASE_INTERVAL_SECONDS,
    COINBASE_PROVIDER_VERSION,
    CoinbasePublicMarketDataProvider,
)
from atlas.investment.market_data.contracts import (
    MARKET_DATA_CONTRACT_VERSION,
    MarketBar,
    QuoteSnapshot,
)
from atlas.investment.market_data.diagnostics import (
    diagnose_provider,
)
from atlas.investment.market_data.http import (
    HttpJsonResponse,
    JsonHttpTransport,
    UrllibJsonTransport,
)
from atlas.investment.market_data.providers import (
    MarketDataProvider,
    ProviderCapabilities,
    StaticMarketDataProvider,
)
from atlas.investment.market_data.service import (
    MARKET_DATA_SERVICE_VERSION,
    MarketDataRouter,
    evaluate_bar_series,
    evaluate_quote_quality,
    reference_prices_from_snapshot,
)
from atlas.investment.market_data.store import (
    LATEST_MARKET_SNAPSHOT_JSON,
    MARKET_DATA_AUDIT_JSONL,
    load_market_snapshot,
    read_market_data_audit,
    validate_market_data_audit,
    write_market_snapshot,
)


__all__ = [
    "COINBASE_BASE_URL",
    "COINBASE_INTERVAL_SECONDS",
    "COINBASE_PROVIDER_VERSION",
    "CacheStatistics",
    "CachedMarketDataProvider",
    "CoinbasePublicMarketDataProvider",
    "HttpJsonResponse",
    "JsonHttpTransport",
    "LATEST_MARKET_SNAPSHOT_JSON",
    "MARKET_DATA_AUDIT_JSONL",
    "MARKET_DATA_CONTRACT_VERSION",
    "MARKET_DATA_SERVICE_VERSION",
    "MarketBar",
    "MarketDataProvider",
    "MarketDataRouter",
    "ProviderCapabilities",
    "QuoteSnapshot",
    "StaticMarketDataProvider",
    "UrllibJsonTransport",
    "diagnose_provider",
    "evaluate_bar_series",
    "evaluate_quote_quality",
    "load_market_snapshot",
    "read_market_data_audit",
    "reference_prices_from_snapshot",
    "validate_market_data_audit",
    "write_market_snapshot",
]
