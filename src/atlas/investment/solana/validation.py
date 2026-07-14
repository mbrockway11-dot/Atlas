"""Validation helpers for Atlas G.24."""

from __future__ import annotations

import re

from .errors import SolanaValidationError

_BASE58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]+$")


def validate_public_key(value: str) -> str:
    public_key = value.strip()
    if not 32 <= len(public_key) <= 44:
        raise SolanaValidationError("Solana public key length is invalid")
    if not _BASE58.fullmatch(public_key):
        raise SolanaValidationError("Solana public key must be base58")
    return public_key


def validate_network(value: str) -> str:
    network = value.strip().lower()
    if network not in {"mainnet-beta", "devnet", "testnet"}:
        raise SolanaValidationError(f"Unsupported Solana network: {value}")
    return network


def rpc_url_for_network(network: str) -> str:
    network = validate_network(network)
    return f"https://api.{network}.solana.com"


__all__ = ["rpc_url_for_network", "validate_network", "validate_public_key"]
