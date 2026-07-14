"""Market-monitor errors for Atlas G.23."""


class MarketMonitorError(RuntimeError):
    """Base market-monitor error."""


class MarketDataValidationError(MarketMonitorError):
    """A provider payload or normalized ticker is invalid."""


class MarketDataStaleError(MarketMonitorError):
    """Ticker data exceeded the configured freshness threshold."""


class VenueUnavailableError(MarketMonitorError):
    """Provider payload indicates an unavailable venue."""


__all__ = [
    "MarketDataStaleError",
    "MarketDataValidationError",
    "MarketMonitorError",
    "VenueUnavailableError",
]
