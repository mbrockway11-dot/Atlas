"""Sandbox-only CCXT broker adapter for Atlas.

CCXT Broker Adapter V1 provides provider-neutral sandbox execution for
supported cryptocurrency exchanges. The adapter deliberately refuses
non-sandbox submission and never advertises live-trading capability.

Credentials are not stored by Atlas. They may be passed directly or loaded
from environment variables by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import time
from typing import Any, Mapping, Protocol

from .base import BrokerAdapter, ExecutionModeGate
from .capabilities import validate_order_capabilities
from .contracts import (
    BrokerAccountSnapshot,
    BrokerCapabilities,
    BrokerHealthState,
    BrokerHealthStatus,
    BrokerOrderRequest,
    BrokerOrderResponse,
    BrokerOrderStatus,
    BrokerOrderType,
    BrokerPosition,
    BrokerSide,
    BrokerTimeInForce,
)
from .errors import (
    BrokerCapabilityError,
    BrokerConfigurationError,
    BrokerDuplicateOrderError,
    BrokerError,
    BrokerExecutionModeError,
    BrokerNotFoundError,
    BrokerValidationError,
)
from .mock import PaperOnlyExecutionGate


class CCXTExchangeProtocol(Protocol):
    """Minimal CCXT exchange surface required by Atlas."""

    id: str
    has: Mapping[str, Any]

    def set_sandbox_mode(self, enabled: bool) -> None:
        ...

    def load_markets(self) -> Mapping[str, Any]:
        ...

    def fetch_balance(self) -> Mapping[str, Any]:
        ...

    def fetch_positions(
        self,
        symbols: list[str] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> list[Mapping[str, Any]]:
        ...

    def fetch_open_orders(
        self,
        symbol: str | None = None,
        since: int | None = None,
        limit: int | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> list[Mapping[str, Any]]:
        ...

    def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: float | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        ...

    def cancel_order(
        self,
        order_id: str,
        symbol: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        ...

    def fetch_order(
        self,
        order_id: str,
        symbol: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        ...

    def edit_order(
        self,
        order_id: str,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: float | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        ...


@dataclass(frozen=True)
class CCXTBrokerConfig:
    """Safe CCXT adapter configuration."""

    exchange_id: str
    account_id: str = ""
    quote_currency: str = "USD"
    sandbox: bool = True
    paper_only: bool = True
    live_execution: bool = False
    enable_rate_limit: bool = True
    default_type: str = "spot"
    timeout_ms: int = 15_000
    symbol_separator: str = "/"
    client_order_id_parameter: str = "clientOrderId"

    def __post_init__(self) -> None:
        exchange_id = self.exchange_id.strip().lower()

        if not exchange_id:
            raise BrokerConfigurationError(
                "exchange_id is required"
            )

        if not self.sandbox:
            raise BrokerConfigurationError(
                "CCXT Broker Adapter V1 requires sandbox=True"
            )

        if not self.paper_only:
            raise BrokerConfigurationError(
                "CCXT Broker Adapter V1 must remain paper-only"
            )

        if self.live_execution:
            raise BrokerConfigurationError(
                "CCXT Broker Adapter V1 cannot enable live execution"
            )

        if self.timeout_ms < 1:
            raise BrokerConfigurationError(
                "timeout_ms must be positive"
            )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atlas_symbol_to_ccxt(symbol: str) -> str:
    """Convert Atlas symbols such as SOL-USD to CCXT SOL/USD."""

    value = str(symbol).strip().upper()

    if not value:
        raise BrokerValidationError(
            "symbol is required"
        )

    value = value.replace("_", "/").replace("-", "/")

    while "//" in value:
        value = value.replace("//", "/")

    if "/" not in value:
        raise BrokerValidationError(
            f"CCXT symbol requires base and quote currency: {symbol!r}"
        )

    base, quote, *rest = value.split("/")

    if rest or not base or not quote:
        raise BrokerValidationError(
            f"Invalid CCXT symbol: {symbol!r}"
        )

    return f"{base}/{quote}"


def ccxt_symbol_to_atlas(symbol: str) -> str:
    value = str(symbol).strip().upper().replace("/", "-")

    if not value:
        raise BrokerValidationError(
            "Provider symbol is empty"
        )

    return value


def normalize_ccxt_status(value: Any) -> BrokerOrderStatus:
    status = str(value or "").strip().lower()

    mapping = {
        "": BrokerOrderStatus.NEW,
        "new": BrokerOrderStatus.NEW,
        "pending": BrokerOrderStatus.NEW,
        "open": BrokerOrderStatus.ACCEPTED,
        "accepted": BrokerOrderStatus.ACCEPTED,
        "partially_filled": BrokerOrderStatus.PARTIALLY_FILLED,
        "partial": BrokerOrderStatus.PARTIALLY_FILLED,
        "filled": BrokerOrderStatus.FILLED,
        "closed": BrokerOrderStatus.FILLED,
        "canceled": BrokerOrderStatus.CANCELLED,
        "cancelled": BrokerOrderStatus.CANCELLED,
        "rejected": BrokerOrderStatus.REJECTED,
        "expired": BrokerOrderStatus.EXPIRED,
        "replaced": BrokerOrderStatus.REPLACED,
    }

    try:
        return mapping[status]
    except KeyError as exc:
        raise BrokerValidationError(
            f"Unknown CCXT order status: {value!r}"
        ) from exc


def normalize_ccxt_side(value: Any) -> BrokerSide:
    normalized = str(value or "").strip().upper()

    try:
        return BrokerSide(normalized)
    except ValueError as exc:
        raise BrokerValidationError(
            f"Unknown CCXT order side: {value!r}"
        ) from exc


def normalize_ccxt_order_type(value: Any) -> BrokerOrderType:
    normalized = (
        str(value or "")
        .strip()
        .upper()
        .replace("-", "_")
    )

    aliases = {
        "STOP_LOSS": BrokerOrderType.STOP,
        "STOP_LOSS_LIMIT": BrokerOrderType.STOP_LIMIT,
        "TAKE_PROFIT": BrokerOrderType.STOP,
        "TAKE_PROFIT_LIMIT": BrokerOrderType.STOP_LIMIT,
    }

    if normalized in aliases:
        return aliases[normalized]

    try:
        return BrokerOrderType(normalized)
    except ValueError as exc:
        raise BrokerValidationError(
            f"Unknown CCXT order type: {value!r}"
        ) from exc


def milliseconds_to_iso(value: Any) -> str:
    try:
        milliseconds = int(value)
    except (TypeError, ValueError):
        return utc_now()

    return datetime.fromtimestamp(
        milliseconds / 1000.0,
        tz=timezone.utc,
    ).isoformat()


def build_ccxt_exchange(
    config: CCXTBrokerConfig,
    *,
    api_key: str | None = None,
    api_secret: str | None = None,
    password: str | None = None,
    uid: str | None = None,
) -> CCXTExchangeProtocol:
    """Construct a real CCXT exchange instance.

    This function does not submit an order. Sandbox mode is applied
    immediately and is mandatory in V1.
    """

    try:
        import ccxt
    except ImportError as exc:
        raise BrokerConfigurationError(
            "ccxt is not installed. Run: python -m pip install ccxt"
        ) from exc

    exchange_class = getattr(
        ccxt,
        config.exchange_id.strip().lower(),
        None,
    )

    if exchange_class is None:
        raise BrokerConfigurationError(
            f"Unknown CCXT exchange: {config.exchange_id}"
        )

    options: dict[str, Any] = {
        "enableRateLimit": config.enable_rate_limit,
        "timeout": config.timeout_ms,
        "options": {
            "defaultType": config.default_type,
        },
    }

    if api_key:
        options["apiKey"] = api_key

    if api_secret:
        options["secret"] = api_secret

    if password:
        options["password"] = password

    if uid:
        options["uid"] = uid

    exchange = exchange_class(options)

    try:
        exchange.set_sandbox_mode(True)
    except Exception as exc:
        raise BrokerConfigurationError(
            f"{config.exchange_id} did not accept sandbox mode"
        ) from exc

    return exchange


class CCXTBrokerAdapter(BrokerAdapter):
    """Atlas sandbox adapter backed by a CCXT exchange instance."""

    def __init__(
        self,
        *,
        config: CCXTBrokerConfig,
        exchange: CCXTExchangeProtocol | None = None,
        execution_gate: ExecutionModeGate | None = None,
        api_key: str | None = None,
        api_secret: str | None = None,
        password: str | None = None,
        uid: str | None = None,
    ) -> None:
        self._config = config
        self._execution_gate = (
            execution_gate
            or PaperOnlyExecutionGate()
        )

        self._exchange = (
            exchange
            if exchange is not None
            else build_ccxt_exchange(
                config,
                api_key=api_key,
                api_secret=api_secret,
                password=password,
                uid=uid,
            )
        )

        if exchange is not None:
            try:
                self._exchange.set_sandbox_mode(True)
            except Exception as exc:
                raise BrokerConfigurationError(
                    "Injected exchange rejected sandbox mode"
                ) from exc

        self._submitted_client_ids: set[str] = set()
        self._order_symbols: dict[str, str] = {}

        exchange_name = str(
            getattr(
                self._exchange,
                "id",
                config.exchange_id,
            )
        ).strip().lower()

        has = dict(
            getattr(
                self._exchange,
                "has",
                {},
            )
            or {}
        )

        self._capabilities = BrokerCapabilities(
            provider=f"ccxt:{exchange_name}",
            paper_only=True,
            live_trading=False,
            supports_market_orders=True,
            supports_limit_orders=True,
            supports_stop_orders=False,
            supports_stop_limit_orders=False,
            supports_cancel=bool(
                has.get("cancelOrder", True)
            ),
            supports_replace=bool(
                has.get("editOrder", False)
            ),
            supports_fractional_quantity=True,
            supports_shorting=False,
            supported_asset_classes=("CRYPTO",),
            supported_time_in_force=(
                BrokerTimeInForce.GTC.value,
                BrokerTimeInForce.IOC.value,
                BrokerTimeInForce.FOK.value,
            ),
        )

    @property
    def provider_name(self) -> str:
        return self._capabilities.provider

    @property
    def capabilities(self) -> BrokerCapabilities:
        return self._capabilities

    def get_account(self) -> BrokerAccountSnapshot:
        payload = self._call(
            "fetch_balance",
            self._exchange.fetch_balance,
        )

        free = self._currency_value(
            payload,
            "free",
            self._config.quote_currency,
        )

        total = self._currency_value(
            payload,
            "total",
            self._config.quote_currency,
            default=free,
        )

        used = self._currency_value(
            payload,
            "used",
            self._config.quote_currency,
            default=max(total - free, 0.0),
        )

        return BrokerAccountSnapshot(
            account_id=(
                self._config.account_id
                or f"ccxt-{self._config.exchange_id}-sandbox"
            ),
            currency=self._config.quote_currency.upper(),
            cash=free,
            equity=total,
            buying_power=free,
            gross_exposure=max(used, 0.0),
            net_exposure=max(total - free, 0.0),
            paper_only=True,
            live_execution=False,
        )

    def get_positions(self) -> list[BrokerPosition]:
        has = dict(
            getattr(
                self._exchange,
                "has",
                {},
            )
            or {}
        )

        if not has.get("fetchPositions"):
            return self._spot_balance_positions()

        payload = self._call(
            "fetch_positions",
            self._exchange.fetch_positions,
            None,
            {},
        )

        if not isinstance(payload, list):
            raise BrokerValidationError(
                "CCXT fetch_positions must return a list"
            )

        positions: list[BrokerPosition] = []

        for item in payload:
            if not isinstance(item, Mapping):
                raise BrokerValidationError(
                    "CCXT position entry must be a mapping"
                )

            contracts = self._number(
                item.get(
                    "contracts",
                    item.get("amount", 0.0),
                )
            )

            side = str(
                item.get("side", "")
            ).strip().lower()

            quantity = (
                -abs(contracts)
                if side == "short"
                else contracts
            )

            entry_price = self._number(
                item.get(
                    "entryPrice",
                    item.get("average", 0.0),
                )
            )

            mark_price = self._number(
                item.get(
                    "markPrice",
                    item.get("last", entry_price),
                ),
                default=entry_price,
            )

            market_value = self._number(
                item.get(
                    "notional",
                    quantity * mark_price,
                ),
                default=quantity * mark_price,
            )

            positions.append(
                BrokerPosition(
                    symbol=ccxt_symbol_to_atlas(
                        str(item["symbol"])
                    ),
                    quantity=quantity,
                    average_price=entry_price,
                    market_value=market_value,
                    unrealized_pnl=self._number(
                        item.get(
                            "unrealizedPnl",
                            0.0,
                        )
                    ),
                    realized_pnl=self._number(
                        item.get(
                            "realizedPnl",
                            0.0,
                        )
                    ),
                )
            )

        return sorted(
            positions,
            key=lambda position: position.symbol,
        )

    def get_open_orders(self) -> list[BrokerOrderResponse]:
        payload = self._call(
            "fetch_open_orders",
            self._exchange.fetch_open_orders,
            None,
            None,
            None,
            {},
        )

        if not isinstance(payload, list):
            raise BrokerValidationError(
                "CCXT fetch_open_orders must return a list"
            )

        return [
            self._normalize_order(item)
            for item in payload
        ]

    def submit_order(
        self,
        request: BrokerOrderRequest,
    ) -> BrokerOrderResponse:
        self._execution_gate.assert_broker_submission_allowed(
            paper_only=True
        )

        self._validate_request(request)
        validate_order_capabilities(
            request,
            self.capabilities,
        )

        if request.client_order_id in self._submitted_client_ids:
            raise BrokerDuplicateOrderError(
                "Duplicate client_order_id: "
                f"{request.client_order_id}"
            )

        symbol = atlas_symbol_to_ccxt(
            request.symbol
        )

        params = self._build_order_params(
            request
        )

        payload = self._call(
            "create_order",
            self._exchange.create_order,
            symbol,
            request.order_type.value.lower(),
            request.side.value.lower(),
            float(request.quantity),
            (
                float(request.limit_price)
                if request.limit_price is not None
                else None
            ),
            params,
        )

        response = self._normalize_order(
            payload,
            fallback_request=request,
        )

        self._submitted_client_ids.add(
            request.client_order_id
        )

        self._order_symbols[
            response.broker_order_id
        ] = symbol

        return response

    def cancel_order(
        self,
        broker_order_id: str,
    ) -> BrokerOrderResponse:
        if not self.capabilities.supports_cancel:
            raise BrokerCapabilityError(
                "Cancel is not supported"
            )

        symbol = self._order_symbols.get(
            broker_order_id
        )

        payload = self._call(
            "cancel_order",
            self._exchange.cancel_order,
            broker_order_id,
            symbol,
            {},
        )

        response = self._normalize_order(
            payload,
            fallback_order_id=broker_order_id,
            fallback_symbol=symbol,
            fallback_status=BrokerOrderStatus.CANCELLED,
        )

        return response

    def replace_order(
        self,
        broker_order_id: str,
        request: BrokerOrderRequest,
    ) -> BrokerOrderResponse:
        if not self.capabilities.supports_replace:
            raise BrokerCapabilityError(
                "Exchange does not support edit_order"
            )

        self._execution_gate.assert_broker_submission_allowed(
            paper_only=True
        )

        self._validate_request(request)
        validate_order_capabilities(
            request,
            self.capabilities,
        )

        if (
            request.client_order_id
            in self._submitted_client_ids
        ):
            raise BrokerDuplicateOrderError(
                "Duplicate client_order_id: "
                f"{request.client_order_id}"
            )

        symbol = atlas_symbol_to_ccxt(
            request.symbol
        )

        payload = self._call(
            "edit_order",
            self._exchange.edit_order,
            broker_order_id,
            symbol,
            request.order_type.value.lower(),
            request.side.value.lower(),
            float(request.quantity),
            (
                float(request.limit_price)
                if request.limit_price is not None
                else None
            ),
            self._build_order_params(request),
        )

        response = self._normalize_order(
            payload,
            fallback_request=request,
            fallback_order_id=broker_order_id,
            fallback_status=BrokerOrderStatus.REPLACED,
        )

        self._submitted_client_ids.add(
            request.client_order_id
        )

        self._order_symbols[
            response.broker_order_id
        ] = symbol

        return response

    def get_order(
        self,
        broker_order_id: str,
    ) -> BrokerOrderResponse:
        symbol = self._order_symbols.get(
            broker_order_id
        )

        payload = self._call(
            "fetch_order",
            self._exchange.fetch_order,
            broker_order_id,
            symbol,
            {},
        )

        return self._normalize_order(
            payload,
            fallback_order_id=broker_order_id,
            fallback_symbol=symbol,
        )

    def health_check(self) -> BrokerHealthStatus:
        started = time.perf_counter()

        try:
            self._call(
                "load_markets",
                self._exchange.load_markets,
            )

            elapsed = int(
                (
                    time.perf_counter()
                    - started
                )
                * 1000
            )

            return BrokerHealthStatus(
                provider=self.provider_name,
                state=BrokerHealthState.HEALTHY,
                checked_at=utc_now(),
                message=(
                    "CCXT sandbox connection available"
                ),
                latency_ms=elapsed,
                paper_only=True,
                live_execution=False,
            )
        except BrokerError as exc:
            elapsed = int(
                (
                    time.perf_counter()
                    - started
                )
                * 1000
            )

            return BrokerHealthStatus(
                provider=self.provider_name,
                state=BrokerHealthState.UNAVAILABLE,
                checked_at=utc_now(),
                message=str(exc),
                latency_ms=elapsed,
                paper_only=True,
                live_execution=False,
            )

    def _spot_balance_positions(
        self,
    ) -> list[BrokerPosition]:
        payload = self._call(
            "fetch_balance",
            self._exchange.fetch_balance,
        )

        total = payload.get(
            "total",
            {}
        )

        if not isinstance(total, Mapping):
            return []

        quote = self._config.quote_currency.upper()
        positions: list[BrokerPosition] = []

        for currency, raw_quantity in total.items():
            currency_name = str(currency).upper()

            if currency_name == quote:
                continue

            quantity = self._number(
                raw_quantity
            )

            if quantity == 0.0:
                continue

            positions.append(
                BrokerPosition(
                    symbol=f"{currency_name}-{quote}",
                    quantity=quantity,
                    average_price=0.0,
                    market_value=0.0,
                    unrealized_pnl=0.0,
                    realized_pnl=0.0,
                )
            )

        return sorted(
            positions,
            key=lambda position: position.symbol,
        )

    def _build_order_params(
        self,
        request: BrokerOrderRequest,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            self._config.client_order_id_parameter:
                request.client_order_id,
            "timeInForce":
                request.time_in_force.value,
        }

        if request.reduce_only:
            params["reduceOnly"] = True

        if request.stop_price is not None:
            params["stopPrice"] = float(
                request.stop_price
            )

        metadata = dict(
            request.metadata
            or {}
        )

        safe_metadata = metadata.get(
            "ccxt_params",
            {}
        )

        if safe_metadata:
            if not isinstance(
                safe_metadata,
                Mapping,
            ):
                raise BrokerValidationError(
                    "metadata.ccxt_params must be a mapping"
                )

            params.update(
                dict(safe_metadata)
            )

        params["atlasPaperOnly"] = True
        params["atlasLiveExecution"] = False

        return params

    def _normalize_order(
        self,
        payload: Mapping[str, Any],
        *,
        fallback_request: BrokerOrderRequest | None = None,
        fallback_order_id: str | None = None,
        fallback_symbol: str | None = None,
        fallback_status: BrokerOrderStatus | None = None,
    ) -> BrokerOrderResponse:
        if not isinstance(payload, Mapping):
            raise BrokerValidationError(
                "CCXT order response must be a mapping"
            )

        order_id = str(
            payload.get("id")
            or fallback_order_id
            or ""
        )

        if not order_id:
            raise BrokerValidationError(
                "CCXT order response has no order ID"
            )

        raw_symbol = (
            payload.get("symbol")
            or fallback_symbol
            or (
                fallback_request.symbol
                if fallback_request is not None
                else ""
            )
        )

        symbol = ccxt_symbol_to_atlas(
            str(raw_symbol)
        )

        client_order_id = str(
            payload.get("clientOrderId")
            or payload.get("client_order_id")
            or (
                fallback_request.client_order_id
                if fallback_request is not None
                else ""
            )
        )

        raw_side = (
            payload.get("side")
            or (
                fallback_request.side.value
                if fallback_request is not None
                else ""
            )
        )

        raw_type = (
            payload.get("type")
            or payload.get("orderType")
            or (
                fallback_request.order_type.value
                if fallback_request is not None
                else ""
            )
        )

        quantity = self._number(
            payload.get(
                "amount",
                (
                    fallback_request.quantity
                    if fallback_request is not None
                    else 0.0
                ),
            )
        )

        filled = self._number(
            payload.get(
                "filled",
                0.0,
            )
        )

        raw_status = payload.get("status")

        status = (
            normalize_ccxt_status(raw_status)
            if raw_status is not None
            else (
                fallback_status
                or BrokerOrderStatus.ACCEPTED
            )
        )

        average_value = payload.get(
            "average"
        )

        average = (
            None
            if average_value is None
            else self._number(
                average_value
            )
        )

        submitted_at = str(
            payload.get("datetime")
            or milliseconds_to_iso(
                payload.get("timestamp")
            )
        )

        updated_at = str(
            payload.get("lastTradeTimestamp")
            and milliseconds_to_iso(
                payload.get("lastTradeTimestamp")
            )
            or submitted_at
        )

        return BrokerOrderResponse(
            broker_order_id=order_id,
            client_order_id=client_order_id,
            symbol=symbol,
            side=normalize_ccxt_side(
                raw_side
            ),
            order_type=normalize_ccxt_order_type(
                raw_type
            ),
            quantity=quantity,
            filled_quantity=filled,
            status=status,
            average_fill_price=average,
            submitted_at=submitted_at,
            updated_at=updated_at,
            paper_only=True,
            live_execution=False,
            raw=dict(payload),
        )

    @staticmethod
    def _currency_value(
        payload: Mapping[str, Any],
        section: str,
        currency: str,
        *,
        default: float = 0.0,
    ) -> float:
        values = payload.get(
            section,
            {}
        )

        if isinstance(values, Mapping):
            return CCXTBrokerAdapter._number(
                values.get(
                    currency.upper(),
                    default,
                ),
                default=default,
            )

        return default

    @staticmethod
    def _number(
        value: Any,
        *,
        default: float = 0.0,
    ) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _validate_request(
        request: BrokerOrderRequest,
    ) -> None:
        if not request.client_order_id.strip():
            raise BrokerValidationError(
                "client_order_id is required"
            )

        atlas_symbol_to_ccxt(
            request.symbol
        )

        if request.quantity <= 0.0:
            raise BrokerValidationError(
                "quantity must be positive"
            )

        if request.order_type == BrokerOrderType.LIMIT:
            if (
                request.limit_price is None
                or request.limit_price <= 0.0
            ):
                raise BrokerValidationError(
                    "Positive limit_price is required for limit orders"
                )

    @staticmethod
    def _call(
        operation: str,
        function: Any,
        *args: Any,
    ) -> Any:
        try:
            return function(*args)
        except BrokerError:
            raise
        except Exception as exc:
            message = str(exc)

            lowered = message.lower()

            if (
                "not found" in lowered
                or "unknown order" in lowered
            ):
                raise BrokerNotFoundError(
                    f"CCXT {operation} failed: {message}"
                ) from exc

            if (
                "authentication" in lowered
                or "api key" in lowered
                or "permission" in lowered
                or "unauthorized" in lowered
            ):
                raise BrokerConfigurationError(
                    f"CCXT {operation} authentication failed: {message}"
                ) from exc

            raise BrokerError(
                f"CCXT {operation} failed: {message}"
            ) from exc


__all__ = [
    "CCXTBrokerAdapter",
    "CCXTBrokerConfig",
    "CCXTExchangeProtocol",
    "atlas_symbol_to_ccxt",
    "build_ccxt_exchange",
    "ccxt_symbol_to_atlas",
    "normalize_ccxt_order_type",
    "normalize_ccxt_side",
    "normalize_ccxt_status",
]
