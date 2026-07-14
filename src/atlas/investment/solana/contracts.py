"""Read-only Solana and Jupiter contracts for Atlas G.24."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

SCHEMA_VERSION = "g24.solana_read_only.v1"


@dataclass(frozen=True)
class WalletRegistration:
    wallet_id: str
    public_key: str
    label: str
    network: str = "mainnet-beta"
    read_only: bool = True
    signing_enabled: bool = False
    submission_enabled: bool = False


@dataclass(frozen=True)
class NativeBalance:
    public_key: str
    lamports: int
    sol: float
    slot: int
    commitment: str
    read_only: bool = True


@dataclass(frozen=True)
class TokenBalance:
    token_account: str
    mint: str
    owner: str
    raw_amount: str
    decimals: int
    ui_amount: float
    state: str


@dataclass(frozen=True)
class WalletSnapshot:
    wallet: WalletRegistration
    native_balance: NativeBalance
    token_balances: tuple[TokenBalance, ...]
    captured_at: str
    record_hash: str = ""
    previous_record_hash: str = ""
    read_only: bool = True
    signing_enabled: bool = False
    submission_enabled: bool = False


@dataclass(frozen=True)
class JupiterQuoteRequest:
    input_mint: str
    output_mint: str
    amount: int
    slippage_bps: int = 50
    swap_mode: str = "ExactIn"
    only_direct_routes: bool = False


@dataclass(frozen=True)
class JupiterQuote:
    input_mint: str
    output_mint: str
    in_amount: str
    out_amount: str
    other_amount_threshold: str
    swap_mode: str
    slippage_bps: int
    price_impact_pct: str
    context_slot: int
    time_taken: float
    route_plan: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    read_only: bool = True
    transaction_built: bool = False
    transaction_signed: bool = False
    transaction_submitted: bool = False


@dataclass(frozen=True)
class SimulationResult:
    successful: bool
    error: Any
    logs: tuple[str, ...]
    units_consumed: int | None
    replacement_blockhash: Mapping[str, Any] | None
    accounts: tuple[Mapping[str, Any], ...]
    read_only: bool = True
    transaction_signed: bool = False
    transaction_submitted: bool = False


__all__ = [
    "SCHEMA_VERSION",
    "JupiterQuote",
    "JupiterQuoteRequest",
    "NativeBalance",
    "SimulationResult",
    "TokenBalance",
    "WalletRegistration",
    "WalletSnapshot",
]
