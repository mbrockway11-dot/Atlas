
"""Asset normalization utilities."""

from __future__ import annotations


ASSET_ALIASES = {
    "BTC": "BTC-USD",
    "BTC-USD": "BTC-USD",
    "ETH": "ETH-USD",
    "ETH-USD": "ETH-USD",
    "SOL": "SOL-USD",
    "SOL-USD": "SOL-USD",
    "BNB": "BNB-USD",
    "BNB-USD": "BNB-USD",
    "XRP": "XRP-USD",
    "XRP-USD": "XRP-USD",
    "ADA": "ADA-USD",
    "ADA-USD": "ADA-USD",
    "DOGE": "DOGE-USD",
    "DOGE-USD": "DOGE-USD",
    "LINK": "LINK-USD",
    "LINK-USD": "LINK-USD",
    "AVAX": "AVAX-USD",
    "AVAX-USD": "AVAX-USD",
    "TRX": "TRX-USD",
    "TRX-USD": "TRX-USD",
    "SUI": "SUI-USD",
    "SUI-USD": "SUI-USD",
    "CASH": "CASH",
}


def normalize_asset(asset) -> str | None:
    """Normalize asset symbols to Atlas canonical names."""
    if asset is None:
        return None

    value = str(asset).strip().upper()

    if not value or value in {"NAN", "NONE"}:
        return None

    return ASSET_ALIASES.get(value, value)


def base_asset(asset) -> str | None:
    """Return base symbol from canonical asset."""
    norm = normalize_asset(asset)

    if norm is None:
        return None

    if norm == "CASH":
        return "CASH"

    return norm.replace("-USD", "")
