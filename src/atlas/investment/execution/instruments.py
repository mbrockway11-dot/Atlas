"""Canonical multi-asset instrument registry for Atlas execution.

The registry separates a symbol from its execution assumptions. Spot crypto
and unlevered ETF proxies are eligible for paper execution. Direct futures are
registered for research and pricing, but remain disabled until Atlas supports
contract expiry, rolling, margin, and multiplier-aware account valuation.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


INSTRUMENT_REGISTRY_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_paper_execution"
)

INSTRUMENT_UNIVERSE_JSON = (
    OUTPUT_DIR
    / "instrument_universe.json"
)


VALID_ASSET_CLASSES = {
    "CRYPTO",
    "METALS",
    "ENERGY",
    "EQUITY",
    "RATES",
    "FX",
    "CASH",
}

VALID_INSTRUMENT_TYPES = {
    "SPOT",
    "PERP",
    "ETF",
    "FUTURE",
    "CASH",
}

VALID_MARKET_SESSIONS = {
    "CONTINUOUS",
    "US_EQUITIES",
    "FUTURES",
    "ALWAYS",
}


@dataclass(frozen=True)
class InstrumentSpec:
    """Canonical execution assumptions for one tradable symbol."""

    symbol: str
    asset_class: str
    instrument_type: str
    quote_currency: str = "USD"
    quantity_precision: int = 8
    minimum_quantity: float = 0.0
    minimum_notional: float = 25.0
    contract_multiplier: float = 1.0
    market_session: str = "CONTINUOUS"
    paper_enabled: bool = True
    short_enabled: bool = False
    margin_required: bool = False
    expiry_required: bool = False
    price_source_symbol: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        symbol = str(
            self.symbol
        ).strip().upper()

        asset_class = str(
            self.asset_class
        ).strip().upper()

        instrument_type = str(
            self.instrument_type
        ).strip().upper()

        quote_currency = str(
            self.quote_currency
        ).strip().upper()

        market_session = str(
            self.market_session
        ).strip().upper()

        if not symbol:
            raise ValueError(
                "Instrument symbol is required."
            )

        if (
            asset_class
            not in VALID_ASSET_CLASSES
        ):
            raise ValueError(
                "Unsupported asset class: "
                + asset_class
            )

        if (
            instrument_type
            not in VALID_INSTRUMENT_TYPES
        ):
            raise ValueError(
                "Unsupported instrument type: "
                + instrument_type
            )

        if (
            market_session
            not in VALID_MARKET_SESSIONS
        ):
            raise ValueError(
                "Unsupported market session: "
                + market_session
            )

        if self.quantity_precision < 0:
            raise ValueError(
                "quantity_precision cannot be negative."
            )

        for name in (
            "minimum_quantity",
            "minimum_notional",
            "contract_multiplier",
        ):
            value = float(
                getattr(
                    self,
                    name,
                )
            )

            if (
                not math.isfinite(value)
                or value < 0
            ):
                raise ValueError(
                    f"{name} must be finite and nonnegative."
                )

        if (
            self.contract_multiplier
            <= 0
        ):
            raise ValueError(
                "contract_multiplier must be positive."
            )

        if (
            instrument_type == "FUTURE"
            and not self.margin_required
        ):
            raise ValueError(
                "Futures must require margin."
            )

        if (
            instrument_type == "FUTURE"
            and not self.expiry_required
        ):
            raise ValueError(
                "Futures must require expiry handling."
            )

        object.__setattr__(
            self,
            "symbol",
            symbol,
        )
        object.__setattr__(
            self,
            "asset_class",
            asset_class,
        )
        object.__setattr__(
            self,
            "instrument_type",
            instrument_type,
        )
        object.__setattr__(
            self,
            "quote_currency",
            quote_currency,
        )
        object.__setattr__(
            self,
            "market_session",
            market_session,
        )

        if not self.price_source_symbol:
            object.__setattr__(
                self,
                "price_source_symbol",
                symbol,
            )

    @property
    def leveraged_contract(self) -> bool:
        return bool(
            self.instrument_type
            == "FUTURE"
            or self.contract_multiplier
            != 1.0
            or self.margin_required
        )

    def notional(
        self,
        *,
        quantity: float,
        price: float,
    ) -> float:
        return (
            abs(float(quantity))
            * float(price)
            * self.contract_multiplier
        )

    def normalize_quantity(
        self,
        quantity: float,
    ) -> float:
        value = round(
            abs(float(quantity)),
            self.quantity_precision,
        )

        if (
            value
            < self.minimum_quantity
        ):
            return 0.0

        return value

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result[
            "leveraged_contract"
        ] = self.leveraged_contract
        return result


def crypto(
    symbol: str,
    *,
    minimum_quantity: float,
    minimum_notional: float = 10.0,
    description: str = "",
) -> InstrumentSpec:
    # Modeled as a paper perpetual: short-enabled so long/short strategies (the
    # defensive risk-off hedge) can execute, but contract_multiplier=1.0 and
    # margin_required=False keep leveraged_contract False, so it stays a simple
    # 1x paper instrument -- no live venue, no Jupiter signing.
    return InstrumentSpec(
        symbol=symbol,
        asset_class="CRYPTO",
        instrument_type="PERP",
        quantity_precision=8,
        minimum_quantity=(
            minimum_quantity
        ),
        minimum_notional=(
            minimum_notional
        ),
        market_session="CONTINUOUS",
        paper_enabled=True,
        short_enabled=True,
        description=description,
    )


def etf(
    symbol: str,
    *,
    asset_class: str,
    minimum_notional: float = 25.0,
    description: str = "",
) -> InstrumentSpec:
    return InstrumentSpec(
        symbol=symbol,
        asset_class=asset_class,
        instrument_type="ETF",
        quantity_precision=6,
        minimum_quantity=0.000001,
        minimum_notional=(
            minimum_notional
        ),
        market_session="US_EQUITIES",
        paper_enabled=True,
        short_enabled=False,
        description=description,
    )


def future(
    symbol: str,
    *,
    asset_class: str,
    multiplier: float,
    description: str,
) -> InstrumentSpec:
    return InstrumentSpec(
        symbol=symbol,
        asset_class=asset_class,
        instrument_type="FUTURE",
        quantity_precision=0,
        minimum_quantity=1.0,
        minimum_notional=0.0,
        contract_multiplier=(
            multiplier
        ),
        market_session="FUTURES",
        paper_enabled=False,
        short_enabled=False,
        margin_required=True,
        expiry_required=True,
        description=description,
    )


_CANONICAL_INSTRUMENTS = (
    # Crypto
    crypto(
        "BTC-USD",
        minimum_quantity=0.00000001,
        description="Bitcoin spot proxy",
    ),
    crypto(
        "ETH-USD",
        minimum_quantity=0.00000001,
        description="Ethereum spot proxy",
    ),
    crypto(
        "SOL-USD",
        minimum_quantity=0.000001,
        description="Solana spot proxy",
    ),
    crypto(
        "XRP-USD",
        minimum_quantity=0.000001,
        description="XRP spot proxy",
    ),
    crypto(
        "LINK-USD",
        minimum_quantity=0.000001,
        description="Chainlink spot proxy",
    ),
    crypto(
        "AVAX-USD",
        minimum_quantity=0.000001,
        description="Avalanche spot proxy",
    ),
    crypto(
        "ADA-USD",
        minimum_quantity=0.000001,
        description="Cardano spot proxy",
    ),
    crypto(
        "DOGE-USD",
        minimum_quantity=0.000001,
        description="Dogecoin spot proxy",
    ),
    crypto(
        "LTC-USD",
        minimum_quantity=0.000001,
        description="Litecoin spot proxy",
    ),
    crypto(
        "BCH-USD",
        minimum_quantity=0.000001,
        description="Bitcoin Cash spot proxy",
    ),
    crypto(
        "DOT-USD",
        minimum_quantity=0.000001,
        description="Polkadot spot proxy",
    ),
    crypto(
        "ATOM-USD",
        minimum_quantity=0.000001,
        description="Cosmos spot proxy",
    ),
    crypto(
        "NEAR-USD",
        minimum_quantity=0.000001,
        description="NEAR spot proxy",
    ),
    crypto(
        "AAVE-USD",
        minimum_quantity=0.000001,
        description="Aave spot proxy",
    ),
    crypto(
        "BNB-USD",
        minimum_quantity=0.000001,
        description="BNB spot proxy",
    ),

    # Metals
    etf(
        "GLD",
        asset_class="METALS",
        description="Gold ETF proxy",
    ),
    etf(
        "SLV",
        asset_class="METALS",
        description="Silver ETF proxy",
    ),

    # Energy
    etf(
        "USO",
        asset_class="ENERGY",
        description="WTI crude oil ETF proxy",
    ),
    etf(
        "BNO",
        asset_class="ENERGY",
        description="Brent crude oil ETF proxy",
    ),
    etf(
        "XLE",
        asset_class="ENERGY",
        description="Energy-sector equity ETF",
    ),

    # Broad equity
    etf(
        "SPY",
        asset_class="EQUITY",
        description="S&P 500 ETF",
    ),
    etf(
        "QQQ",
        asset_class="EQUITY",
        description="Nasdaq 100 ETF",
    ),
    etf(
        "IWM",
        asset_class="EQUITY",
        description="Russell 2000 ETF",
    ),
    etf(
        "DIA",
        asset_class="EQUITY",
        description="Dow Jones ETF",
    ),

    # Rates and defense
    etf(
        "TLT",
        asset_class="RATES",
        description="Long-duration Treasury ETF",
    ),
    etf(
        "IEF",
        asset_class="RATES",
        description="Intermediate Treasury ETF",
    ),
    etf(
        "SHY",
        asset_class="RATES",
        description="Short-duration Treasury ETF",
    ),
    etf(
        "UUP",
        asset_class="FX",
        description="US dollar index ETF proxy",
    ),

    # Cash
    InstrumentSpec(
        symbol="CASH",
        asset_class="CASH",
        instrument_type="CASH",
        quantity_precision=2,
        minimum_quantity=0.01,
        minimum_notional=0.01,
        market_session="ALWAYS",
        paper_enabled=False,
        description="Uninvested account cash",
    ),

    # Research-only direct futures
    future(
        "GC=F",
        asset_class="METALS",
        multiplier=100.0,
        description=(
            "COMEX gold future; disabled until "
            "margin, expiry, and roll support"
        ),
    ),
    future(
        "SI=F",
        asset_class="METALS",
        multiplier=5000.0,
        description=(
            "COMEX silver future; disabled until "
            "margin, expiry, and roll support"
        ),
    ),
    future(
        "CL=F",
        asset_class="ENERGY",
        multiplier=1000.0,
        description=(
            "WTI crude future; disabled until "
            "margin, expiry, and roll support"
        ),
    ),
    future(
        "BZ=F",
        asset_class="ENERGY",
        multiplier=1000.0,
        description=(
            "Brent crude future; disabled until "
            "margin, expiry, and roll support"
        ),
    ),
    future(
        "NG=F",
        asset_class="ENERGY",
        multiplier=10000.0,
        description=(
            "Natural gas future; disabled until "
            "margin, expiry, and roll support"
        ),
    ),
)


# Liquid Hyperliquid perps beyond the diversified core above. Registered so the
# copy-trade mirror can execute the coins its leaders actually hold -- without
# these, every leader leg on one of these names is rejected UNREGISTERED_INSTRUMENT
# and the mirror silently collapses to the handful of majors (and, since the
# leaders' shorts cluster in these names, to a long-only book). Same paper-perp
# assumptions as the core crypto() specs: short-enabled, 1x, no live venue.
_HYPERLIQUID_MIRROR_PERP_COINS = (
    "HYPE", "SUI", "WLD", "TIA", "SEI", "ARB", "OP", "INJ", "APT", "TON",
    "ENA", "WIF", "PEPE", "BONK", "JUP", "LDO", "RENDER", "TAO", "ORDI",
    "XMR", "ZRO", "VIRTUAL", "LIT", "SKY", "TRUMP", "FARTCOIN", "PENGU", "AI16Z",
)

_CANONICAL_INSTRUMENTS = _CANONICAL_INSTRUMENTS + tuple(
    crypto(
        f"{coin}-USD",
        minimum_quantity=0.000001,
        description=f"{coin} Hyperliquid perp",
    )
    for coin in _HYPERLIQUID_MIRROR_PERP_COINS
)


INSTRUMENT_REGISTRY = {
    instrument.symbol: instrument
    for instrument
    in _CANONICAL_INSTRUMENTS
}


SYMBOL_ALIASES = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SOL": "SOL-USD",
    "XRP": "XRP-USD",
    "LINK": "LINK-USD",
    "AVAX": "AVAX-USD",
    "ADA": "ADA-USD",
    "DOGE": "DOGE-USD",
    "LTC": "LTC-USD",
    "BCH": "BCH-USD",
    "DOT": "DOT-USD",
    "ATOM": "ATOM-USD",
    "NEAR": "NEAR-USD",
    "AAVE": "AAVE-USD",
    "BNB": "BNB-USD",
    "XAU-USD": "GLD",
    "XAG-USD": "SLV",
    "GOLD": "GLD",
    "SILVER": "SLV",
    "WTI": "USO",
    "OIL": "USO",
    "BRENT": "BNO",
    "DXY": "UUP",
    **{coin: f"{coin}-USD" for coin in _HYPERLIQUID_MIRROR_PERP_COINS},
}


def normalize_symbol(
    symbol: str,
) -> str:
    normalized = str(
        symbol
    ).strip().upper()

    return SYMBOL_ALIASES.get(
        normalized,
        normalized,
    )


def get_instrument(
    symbol: str,
    *,
    require_registered: bool = True,
) -> InstrumentSpec | None:
    normalized = normalize_symbol(
        symbol
    )

    result = INSTRUMENT_REGISTRY.get(
        normalized
    )

    if (
        result is None
        and require_registered
    ):
        raise KeyError(
            "UNREGISTERED_INSTRUMENT:"
            + normalized
        )

    return result


def require_paper_instrument(
    symbol: str,
) -> InstrumentSpec:
    instrument = get_instrument(
        symbol
    )

    assert instrument is not None

    if not instrument.paper_enabled:
        raise ValueError(
            "PAPER_EXECUTION_DISABLED:"
            + instrument.symbol
        )

    if instrument.leveraged_contract:
        raise ValueError(
            "LEVERAGED_CONTRACT_UNSUPPORTED:"
            + instrument.symbol
        )

    return instrument


def list_instruments(
    *,
    paper_enabled: bool | None = None,
    asset_class: str | None = None,
) -> list[InstrumentSpec]:
    normalized_class = (
        str(asset_class).upper()
        if asset_class
        else None
    )

    return [
        instrument
        for instrument
        in sorted(
            INSTRUMENT_REGISTRY.values(),
            key=lambda item: (
                item.asset_class,
                item.symbol,
            ),
        )
        if (
            paper_enabled is None
            or instrument.paper_enabled
            == paper_enabled
        )
        and (
            normalized_class is None
            or instrument.asset_class
            == normalized_class
        )
    ]


def validate_instrument_registry() -> list[str]:
    errors: list[str] = []

    symbols = [
        instrument.symbol
        for instrument
        in _CANONICAL_INSTRUMENTS
    ]

    if len(symbols) != len(
        set(symbols)
    ):
        errors.append(
            "DUPLICATE_INSTRUMENT_SYMBOL"
        )

    for instrument in (
        INSTRUMENT_REGISTRY.values()
    ):
        if (
            instrument.paper_enabled
            and instrument.leveraged_contract
        ):
            errors.append(
                "LEVERAGED_INSTRUMENT_PAPER_ENABLED:"
                + instrument.symbol
            )

        if (
            instrument.instrument_type
            == "FUTURE"
            and instrument.paper_enabled
        ):
            errors.append(
                "FUTURE_PAPER_ENABLED:"
                + instrument.symbol
            )

        if (
            instrument.asset_class
            == "CASH"
            and instrument.symbol
            != "CASH"
        ):
            errors.append(
                "INVALID_CASH_INSTRUMENT:"
                + instrument.symbol
            )

    for alias, canonical in (
        SYMBOL_ALIASES.items()
    ):
        if canonical not in (
            INSTRUMENT_REGISTRY
        ):
            errors.append(
                "ALIAS_TARGET_MISSING:"
                + alias
                + "->"
                + canonical
            )

    return errors


def build_instrument_universe_report(
    *,
    write_output: bool = True,
    path: Path = (
        INSTRUMENT_UNIVERSE_JSON
    ),
) -> dict[str, Any]:
    instruments = list_instruments()

    errors = (
        validate_instrument_registry()
    )

    asset_class_counts: dict[
        str,
        int,
    ] = {}

    for instrument in instruments:
        asset_class_counts[
            instrument.asset_class
        ] = (
            asset_class_counts.get(
                instrument.asset_class,
                0,
            )
            + 1
        )

    report = {
        "success": not errors,
        "version": (
            INSTRUMENT_REGISTRY_VERSION
        ),
        "counts": {
            "registered": len(
                instruments
            ),
            "paper_enabled": sum(
                1
                for instrument
                in instruments
                if instrument.paper_enabled
            ),
            "paper_disabled": sum(
                1
                for instrument
                in instruments
                if not instrument.paper_enabled
            ),
            "asset_classes": (
                asset_class_counts
            ),
            "aliases": len(
                SYMBOL_ALIASES
            ),
        },
        "errors": errors,
        "paper_universe": [
            instrument.to_dict()
            for instrument
            in instruments
            if instrument.paper_enabled
        ],
        "research_only_universe": [
            instrument.to_dict()
            for instrument
            in instruments
            if not instrument.paper_enabled
        ],
        "aliases": dict(
            sorted(
                SYMBOL_ALIASES.items()
            )
        ),
        "contract": {
            "spot_crypto_enabled": True,
            "etf_proxies_enabled": True,
            "direct_futures_enabled": False,
            "margin_trading_enabled": False,
            "live_execution_enabled": False,
        },
        "output": str(path),
    }

    if write_output:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = (
            path.with_suffix(
                ".json.tmp"
            )
        )

        temporary.write_text(
            json.dumps(
                report,
                indent=2,
                sort_keys=True,
                default=str,
            ),
            encoding="utf-8",
        )

        temporary.replace(path)

    return report


__all__ = [
    "INSTRUMENT_REGISTRY",
    "INSTRUMENT_REGISTRY_VERSION",
    "INSTRUMENT_UNIVERSE_JSON",
    "InstrumentSpec",
    "SYMBOL_ALIASES",
    "build_instrument_universe_report",
    "get_instrument",
    "list_instruments",
    "normalize_symbol",
    "require_paper_instrument",
    "validate_instrument_registry",
]
