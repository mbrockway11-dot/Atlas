"""Canonical portfolio state and position ledger for Atlas G.21."""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

from .contracts import (
    CashState,
    FillEvent,
    LedgerSide,
    PortfolioSnapshot,
    PositionState,
)
from .errors import (
    DuplicateFillError,
    InsufficientPositionError,
    LedgerValidationError,
)
from .persistence import (
    append_jsonl,
    atomic_write_json,
    compute_hash,
    read_jsonl,
    validate_hash_chain,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_symbol(symbol: str) -> str:
    value = symbol.strip().upper().replace("/", "-").replace("_", "-")
    if not value:
        raise LedgerValidationError("symbol is required")
    return value


class PortfolioLedger:
    def __init__(
        self,
        *,
        portfolio_id: str,
        output_dir: Path,
        starting_cash: Mapping[str, float] | None = None,
    ) -> None:
        if not portfolio_id.strip():
            raise LedgerValidationError("portfolio_id is required")

        self.portfolio_id = portfolio_id
        self.output_dir = output_dir
        self.fill_history_path = output_dir / "fill_history.jsonl"
        self.snapshot_history_path = output_dir / "snapshot_history.jsonl"
        self.latest_snapshot_path = output_dir / "latest_snapshot.json"

        self._cash = {
            currency: float(amount)
            for currency, amount in (starting_cash or {"USD": 0.0}).items()
        }
        self._positions: dict[str, PositionState] = {}
        self._processed_fills: set[str] = set()

    def apply_fill(self, fill: FillEvent) -> PositionState:
        self._validate_fill(fill)

        existing_records = read_jsonl(self.fill_history_path)
        if existing_records:
            validate_hash_chain(existing_records)

        if fill.fill_id in self._processed_fills or any(
            record.get("fill_id") == fill.fill_id
            for record in existing_records
        ):
            raise DuplicateFillError(f"Duplicate fill_id: {fill.fill_id}")

        symbol = normalize_symbol(fill.symbol)
        current = self._positions.get(
            symbol,
            PositionState(
                symbol=symbol,
                quantity=0.0,
                average_cost=0.0,
                market_price=fill.price,
                market_value=0.0,
                realized_pnl=0.0,
                unrealized_pnl=0.0,
                total_fees=0.0,
            ),
        )

        currency = fill.currency.upper()
        self._cash.setdefault(currency, 0.0)

        if fill.side == LedgerSide.BUY:
            new_quantity = current.quantity + fill.quantity
            total_cost = (
                current.average_cost * current.quantity
                + fill.price * fill.quantity
                + fill.fee
            )
            new_average_cost = total_cost / new_quantity
            self._cash[currency] -= fill.price * fill.quantity + fill.fee
            realized_pnl = current.realized_pnl
        else:
            if fill.quantity > current.quantity:
                raise InsufficientPositionError(
                    f"Sell quantity exceeds current position for {symbol}"
                )
            new_quantity = current.quantity - fill.quantity
            realized_delta = (
                fill.price - current.average_cost
            ) * fill.quantity - fill.fee
            realized_pnl = current.realized_pnl + realized_delta
            self._cash[currency] += fill.price * fill.quantity - fill.fee
            new_average_cost = current.average_cost if new_quantity > 0 else 0.0

        updated = PositionState(
            symbol=symbol,
            quantity=new_quantity,
            average_cost=new_average_cost,
            market_price=fill.price,
            market_value=new_quantity * fill.price,
            realized_pnl=realized_pnl,
            unrealized_pnl=(
                (fill.price - new_average_cost) * new_quantity
                if new_quantity > 0
                else 0.0
            ),
            total_fees=current.total_fees + fill.fee,
        )
        self._positions[symbol] = updated
        self._processed_fills.add(fill.fill_id)

        previous_hash = (
            existing_records[-1]["record_hash"] if existing_records else ""
        )
        payload = asdict(fill)
        payload["symbol"] = symbol
        payload["previous_record_hash"] = previous_hash
        payload["record_hash"] = ""
        payload["record_hash"] = compute_hash(payload)
        append_jsonl(self.fill_history_path, payload)

        return updated

    def mark_prices(self, prices: Mapping[str, float]) -> None:
        for raw_symbol, raw_price in prices.items():
            symbol = normalize_symbol(raw_symbol)
            price = float(raw_price)
            if price <= 0:
                raise LedgerValidationError(
                    f"Market price must be positive for {symbol}"
                )
            current = self._positions.get(symbol)
            if current is None:
                continue
            self._positions[symbol] = replace(
                current,
                market_price=price,
                market_value=current.quantity * price,
                unrealized_pnl=(price - current.average_cost) * current.quantity,
            )

    def snapshot(self, *, as_of: str | None = None) -> PortfolioSnapshot:
        records = read_jsonl(self.snapshot_history_path)
        if records:
            validate_hash_chain(records)

        positions = tuple(
            self._positions[symbol] for symbol in sorted(self._positions)
        )
        cash = tuple(
            CashState(currency=currency, balance=self._cash[currency])
            for currency in sorted(self._cash)
        )

        gross_exposure = sum(abs(position.market_value) for position in positions)
        net_exposure = sum(position.market_value for position in positions)
        realized_pnl = sum(position.realized_pnl for position in positions)
        unrealized_pnl = sum(position.unrealized_pnl for position in positions)
        total_fees = sum(position.total_fees for position in positions)
        cash_total = sum(item.balance for item in cash)
        equity = cash_total + net_exposure

        previous_hash = records[-1]["record_hash"] if records else ""
        snapshot = PortfolioSnapshot(
            portfolio_id=self.portfolio_id,
            as_of=as_of or utc_now(),
            cash=cash,
            positions=positions,
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
            equity=equity,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            total_fees=total_fees,
            record_hash="",
            previous_record_hash=previous_hash,
            paper_only=True,
            live_execution=False,
        )
        payload = asdict(snapshot)
        payload["record_hash"] = compute_hash(payload)
        snapshot = replace(snapshot, record_hash=payload["record_hash"])

        atomic_write_json(self.latest_snapshot_path, asdict(snapshot))
        append_jsonl(self.snapshot_history_path, asdict(snapshot))
        return snapshot

    @classmethod
    def replay(
        cls,
        *,
        portfolio_id: str,
        output_dir: Path,
        fills: Iterable[FillEvent],
        starting_cash: Mapping[str, float] | None = None,
    ) -> "PortfolioLedger":
        ledger = cls(
            portfolio_id=portfolio_id,
            output_dir=output_dir,
            starting_cash=starting_cash,
        )
        for fill in fills:
            ledger.apply_fill(fill)
        return ledger

    def positions(self) -> tuple[PositionState, ...]:
        return tuple(
            self._positions[symbol] for symbol in sorted(self._positions)
        )

    def cash(self) -> tuple[CashState, ...]:
        return tuple(
            CashState(currency=currency, balance=self._cash[currency])
            for currency in sorted(self._cash)
        )

    @staticmethod
    def _validate_fill(fill: FillEvent) -> None:
        if not fill.fill_id.strip():
            raise LedgerValidationError("fill_id is required")
        if not fill.broker_order_id.strip():
            raise LedgerValidationError("broker_order_id is required")
        if not fill.client_order_id.strip():
            raise LedgerValidationError("client_order_id is required")
        if fill.quantity <= 0:
            raise LedgerValidationError("quantity must be positive")
        if fill.price <= 0:
            raise LedgerValidationError("price must be positive")
        if fill.fee < 0:
            raise LedgerValidationError("fee cannot be negative")
        if not fill.paper_only or fill.live_execution:
            raise LedgerValidationError("Fill violates paper-only boundary")


__all__ = ["PortfolioLedger", "normalize_symbol", "utc_now"]
