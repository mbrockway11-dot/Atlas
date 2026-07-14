"""Generic REST-compatible paper broker adapter for Atlas G.19.

The adapter never performs network I/O directly. A transport must be injected,
which allows deterministic fixtures, provider sandboxes, or future paper APIs.
Live endpoints and live trading remain disabled.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
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


class RestTransportError(BrokerError):
    """Base transport-layer error."""


class RestRateLimitError(RestTransportError):
    """Provider rate limit was reached."""


class RestAuthenticationError(RestTransportError):
    """Provider rejected authentication."""


class RestServerError(RestTransportError):
    """Provider returned a server-side failure."""


class RestTransport(Protocol):
    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any]:
        """Return a normalized mapping response or raise a transport error."""


@dataclass(frozen=True)
class GenericRestPaperConfig:
    provider: str
    account_path: str = "/paper/account"
    positions_path: str = "/paper/positions"
    orders_path: str = "/paper/orders"
    health_path: str = "/paper/health"
    symbol_separator: str = "-"
    uppercase_symbols: bool = True
    paper_only: bool = True
    live_execution: bool = False
    credentials_required: bool = False
    max_retries: int = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_symbol(
    symbol: str,
    *,
    separator: str = "-",
    uppercase: bool = True,
) -> str:
    value = symbol.strip().replace("/", separator).replace("_", separator)
    while separator * 2 in value:
        value = value.replace(separator * 2, separator)
    if uppercase:
        value = value.upper()
    if not value or value.startswith(separator) or value.endswith(separator):
        raise BrokerValidationError(f"Invalid symbol: {symbol!r}")
    return value


def normalize_order_status(value: str) -> BrokerOrderStatus:
    normalized = value.strip().upper().replace(" ", "_")
    aliases = {
        "OPEN": BrokerOrderStatus.ACCEPTED,
        "PENDING": BrokerOrderStatus.NEW,
        "CANCELED": BrokerOrderStatus.CANCELLED,
        "PARTIAL": BrokerOrderStatus.PARTIALLY_FILLED,
        "DONE": BrokerOrderStatus.FILLED,
    }
    if normalized in aliases:
        return aliases[normalized]
    try:
        return BrokerOrderStatus(normalized)
    except ValueError as exc:
        raise BrokerValidationError(f"Unknown provider order status: {value}") from exc


def normalize_side(value: str) -> BrokerSide:
    normalized = value.strip().upper()
    try:
        return BrokerSide(normalized)
    except ValueError as exc:
        raise BrokerValidationError(f"Unknown provider order side: {value}") from exc


def normalize_order_type(value: str) -> BrokerOrderType:
    normalized = value.strip().upper().replace("-", "_")
    try:
        return BrokerOrderType(normalized)
    except ValueError as exc:
        raise BrokerValidationError(f"Unknown provider order type: {value}") from exc


class GenericRestPaperAdapter(BrokerAdapter):
    def __init__(
        self,
        *,
        config: GenericRestPaperConfig,
        transport: RestTransport,
        execution_gate: ExecutionModeGate | None = None,
    ) -> None:
        if not config.provider.strip():
            raise BrokerConfigurationError("provider is required")
        if not config.paper_only or config.live_execution:
            raise BrokerConfigurationError(
                "GenericRestPaperAdapter must remain paper-only"
            )
        if config.credentials_required:
            raise BrokerConfigurationError(
                "G.19 tests and default adapter may not require credentials"
            )
        if config.max_retries < 0 or config.max_retries > 3:
            raise BrokerConfigurationError("max_retries must be between 0 and 3")

        self._config = config
        self._transport = transport
        self._execution_gate = execution_gate or PaperOnlyExecutionGate()
        self._submitted_client_ids: set[str] = set()
        self._capabilities = BrokerCapabilities(
            provider=config.provider,
            paper_only=True,
            live_trading=False,
            supports_market_orders=True,
            supports_limit_orders=True,
            supports_stop_orders=False,
            supports_stop_limit_orders=False,
            supports_cancel=True,
            supports_replace=True,
            supports_fractional_quantity=True,
            supports_shorting=False,
            supported_asset_classes=("GENERIC", "CRYPTO", "EQUITY"),
        )

    @property
    def provider_name(self) -> str:
        return self._config.provider

    @property
    def capabilities(self) -> BrokerCapabilities:
        return self._capabilities

    def get_account(self) -> BrokerAccountSnapshot:
        payload = self._request("GET", self._config.account_path)
        return BrokerAccountSnapshot(
            account_id=str(payload["account_id"]),
            currency=str(payload.get("currency", "USD")),
            cash=float(payload["cash"]),
            equity=float(payload["equity"]),
            buying_power=float(payload["buying_power"]),
            gross_exposure=float(payload.get("gross_exposure", 0.0)),
            net_exposure=float(payload.get("net_exposure", 0.0)),
            paper_only=True,
            live_execution=False,
        )

    def get_positions(self) -> list[BrokerPosition]:
        payload = self._request("GET", self._config.positions_path)
        items = payload.get("positions", [])
        if not isinstance(items, list):
            raise BrokerValidationError("positions response must contain a list")
        positions: list[BrokerPosition] = []
        for item in items:
            if not isinstance(item, Mapping):
                raise BrokerValidationError("position entry must be an object")
            positions.append(
                BrokerPosition(
                    symbol=normalize_symbol(
                        str(item["symbol"]),
                        separator=self._config.symbol_separator,
                        uppercase=self._config.uppercase_symbols,
                    ),
                    quantity=float(item["quantity"]),
                    average_price=float(item["average_price"]),
                    market_value=float(item["market_value"]),
                    unrealized_pnl=float(item.get("unrealized_pnl", 0.0)),
                    realized_pnl=float(item.get("realized_pnl", 0.0)),
                )
            )
        return positions

    def get_open_orders(self) -> list[BrokerOrderResponse]:
        payload = self._request("GET", self._config.orders_path)
        items = payload.get("orders", [])
        if not isinstance(items, list):
            raise BrokerValidationError("orders response must contain a list")
        return [self._normalize_order(item) for item in items]

    def submit_order(self, request: BrokerOrderRequest) -> BrokerOrderResponse:
        self._execution_gate.assert_broker_submission_allowed(paper_only=True)
        self._validate_request(request)
        validate_order_capabilities(request, self.capabilities)

        if request.client_order_id in self._submitted_client_ids:
            raise BrokerDuplicateOrderError(
                f"Duplicate client_order_id: {request.client_order_id}"
            )

        payload = self._request(
            "POST",
            self._config.orders_path,
            json_body=self._translate_order_request(request),
            headers={"Idempotency-Key": request.client_order_id},
        )
        response = self._normalize_order(payload)
        self._submitted_client_ids.add(request.client_order_id)
        return response

    def cancel_order(self, broker_order_id: str) -> BrokerOrderResponse:
        if not self.capabilities.supports_cancel:
            raise BrokerCapabilityError("Cancel is not supported")
        payload = self._request(
            "POST",
            f"{self._config.orders_path}/{broker_order_id}/cancel",
        )
        return self._normalize_order(payload)

    def replace_order(
        self,
        broker_order_id: str,
        request: BrokerOrderRequest,
    ) -> BrokerOrderResponse:
        if not self.capabilities.supports_replace:
            raise BrokerCapabilityError("Replace is not supported")

        self._execution_gate.assert_broker_submission_allowed(paper_only=True)
        self._validate_request(request)
        validate_order_capabilities(request, self.capabilities)

        payload = self._request(
            "PUT",
            f"{self._config.orders_path}/{broker_order_id}",
            json_body=self._translate_order_request(request),
            headers={"Idempotency-Key": request.client_order_id},
        )
        response = self._normalize_order(payload)
        self._submitted_client_ids.add(request.client_order_id)
        return response

    def get_order(self, broker_order_id: str) -> BrokerOrderResponse:
        try:
            payload = self._request(
                "GET",
                f"{self._config.orders_path}/{broker_order_id}",
            )
        except BrokerNotFoundError:
            raise
        return self._normalize_order(payload)

    def health_check(self) -> BrokerHealthStatus:
        try:
            payload = self._request("GET", self._config.health_path)
            state_value = str(payload.get("state", "HEALTHY")).upper()
            try:
                state = BrokerHealthState(state_value)
            except ValueError:
                state = BrokerHealthState.DEGRADED
            return BrokerHealthStatus(
                provider=self.provider_name,
                state=state,
                checked_at=str(payload.get("checked_at", utc_now())),
                message=str(payload.get("message", "")),
                latency_ms=int(payload.get("latency_ms", 0)),
                paper_only=True,
                live_execution=False,
            )
        except RestTransportError as exc:
            return BrokerHealthStatus(
                provider=self.provider_name,
                state=BrokerHealthState.UNAVAILABLE,
                checked_at=utc_now(),
                message=str(exc),
                latency_ms=0,
                paper_only=True,
                live_execution=False,
            )

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any]:
        attempts = self._config.max_retries + 1
        last_error: Exception | None = None

        for attempt in range(attempts):
            try:
                response = self._transport.request(
                    method,
                    path,
                    json_body=json_body,
                    headers=headers,
                )
                if not isinstance(response, Mapping):
                    raise BrokerValidationError(
                        "Transport response must be a mapping"
                    )
                if response.get("error"):
                    self._raise_provider_error(response)
                return response
            except RestRateLimitError as exc:
                last_error = exc
                if attempt + 1 >= attempts:
                    raise
            except RestTransportError:
                raise

        if last_error is not None:
            raise last_error
        raise RestTransportError("Transport request failed")

    @staticmethod
    def _raise_provider_error(payload: Mapping[str, Any]) -> None:
        code = str(payload.get("code", "")).upper()
        message = str(payload.get("message", "Provider error"))

        if code in {"NOT_FOUND", "ORDER_NOT_FOUND"}:
            raise BrokerNotFoundError(message)
        if code in {"RATE_LIMIT", "TOO_MANY_REQUESTS"}:
            raise RestRateLimitError(message)
        if code in {"AUTH", "UNAUTHORIZED", "FORBIDDEN"}:
            raise RestAuthenticationError(message)
        if code in {"SERVER_ERROR", "UNAVAILABLE"}:
            raise RestServerError(message)
        raise RestTransportError(message)

    def _translate_order_request(
        self,
        request: BrokerOrderRequest,
    ) -> dict[str, Any]:
        return {
            "client_order_id": request.client_order_id,
            "symbol": normalize_symbol(
                request.symbol,
                separator=self._config.symbol_separator,
                uppercase=self._config.uppercase_symbols,
            ),
            "side": request.side.value,
            "order_type": request.order_type.value,
            "quantity": request.quantity,
            "time_in_force": request.time_in_force.value,
            "limit_price": request.limit_price,
            "stop_price": request.stop_price,
            "reduce_only": request.reduce_only,
            "paper_only": True,
            "live_execution": False,
        }

    def _normalize_order(
        self,
        payload: Mapping[str, Any],
    ) -> BrokerOrderResponse:
        timestamp = str(payload.get("updated_at") or payload.get("submitted_at") or utc_now())
        submitted = str(payload.get("submitted_at") or timestamp)

        return BrokerOrderResponse(
            broker_order_id=str(payload["broker_order_id"]),
            client_order_id=str(payload["client_order_id"]),
            symbol=normalize_symbol(
                str(payload["symbol"]),
                separator=self._config.symbol_separator,
                uppercase=self._config.uppercase_symbols,
            ),
            side=normalize_side(str(payload["side"])),
            order_type=normalize_order_type(str(payload["order_type"])),
            quantity=float(payload["quantity"]),
            filled_quantity=float(payload.get("filled_quantity", 0.0)),
            status=normalize_order_status(str(payload["status"])),
            average_fill_price=(
                None
                if payload.get("average_fill_price") is None
                else float(payload["average_fill_price"])
            ),
            submitted_at=submitted,
            updated_at=timestamp,
            paper_only=True,
            live_execution=False,
            raw=dict(payload),
        )

    @staticmethod
    def _validate_request(request: BrokerOrderRequest) -> None:
        if not request.client_order_id.strip():
            raise BrokerValidationError("client_order_id is required")
        if not request.symbol.strip():
            raise BrokerValidationError("symbol is required")
        if request.quantity <= 0:
            raise BrokerValidationError("quantity must be positive")
        if request.order_type == BrokerOrderType.LIMIT:
            if request.limit_price is None or request.limit_price <= 0:
                raise BrokerValidationError(
                    "Positive limit_price is required for limit orders"
                )


__all__ = [
    "GenericRestPaperAdapter",
    "GenericRestPaperConfig",
    "RestAuthenticationError",
    "RestRateLimitError",
    "RestServerError",
    "RestTransport",
    "RestTransportError",
    "normalize_order_status",
    "normalize_order_type",
    "normalize_side",
    "normalize_symbol",
]
