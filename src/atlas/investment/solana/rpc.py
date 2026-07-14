"""Read-only Solana JSON-RPC client for Atlas G.24."""

from __future__ import annotations

import itertools
from typing import Any, Mapping

from .contracts import NativeBalance, SimulationResult, TokenBalance
from .errors import SigningDisabledError, SolanaRpcError
from .transport import JsonTransport, UrllibJsonTransport
from .validation import validate_public_key

TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"


class SolanaReadOnlyRpcClient:
    def __init__(
        self,
        *,
        rpc_url: str,
        transport: JsonTransport | None = None,
        commitment: str = "confirmed",
    ) -> None:
        self.rpc_url = rpc_url
        self.transport = transport or UrllibJsonTransport()
        self.commitment = commitment
        self._ids = itertools.count(1)

    def _rpc(self, method: str, params: list[Any]) -> Mapping[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": next(self._ids),
            "method": method,
            "params": params,
        }
        response = self.transport.post_json(self.rpc_url, payload)
        if response.get("error") is not None:
            raise SolanaRpcError(str(response["error"]))
        result = response.get("result")
        if not isinstance(result, dict):
            raise SolanaRpcError(f"Malformed RPC result for {method}")
        return result

    def get_native_balance(self, public_key: str) -> NativeBalance:
        public_key = validate_public_key(public_key)
        result = self._rpc(
            "getBalance",
            [public_key, {"commitment": self.commitment}],
        )
        lamports = int(result["value"])
        context = result.get("context", {})
        return NativeBalance(
            public_key=public_key,
            lamports=lamports,
            sol=lamports / 1_000_000_000,
            slot=int(context.get("slot", 0)),
            commitment=self.commitment,
            read_only=True,
        )

    def get_token_balances(self, public_key: str) -> tuple[TokenBalance, ...]:
        public_key = validate_public_key(public_key)
        result = self._rpc(
            "getTokenAccountsByOwner",
            [
                public_key,
                {"programId": TOKEN_PROGRAM_ID},
                {
                    "commitment": self.commitment,
                    "encoding": "jsonParsed",
                },
            ],
        )
        values = result.get("value", [])
        if not isinstance(values, list):
            raise SolanaRpcError("Token-account result must be a list")

        balances: list[TokenBalance] = []
        for item in values:
            try:
                info = item["account"]["data"]["parsed"]["info"]
                token_amount = info["tokenAmount"]
                balances.append(
                    TokenBalance(
                        token_account=str(item["pubkey"]),
                        mint=str(info["mint"]),
                        owner=str(info["owner"]),
                        raw_amount=str(token_amount["amount"]),
                        decimals=int(token_amount["decimals"]),
                        ui_amount=float(
                            token_amount.get("uiAmount")
                            if token_amount.get("uiAmount") is not None
                            else token_amount.get("uiAmountString", 0)
                        ),
                        state=str(info.get("state", "unknown")),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise SolanaRpcError("Malformed token-account payload") from exc
        return tuple(balances)

    def simulate_unsigned_transaction(
        self,
        encoded_transaction: str,
        *,
        sig_verify: bool = False,
        replace_recent_blockhash: bool = True,
    ) -> SimulationResult:
        if not encoded_transaction.strip():
            raise SolanaRpcError("encoded_transaction is required")
        result = self._rpc(
            "simulateTransaction",
            [
                encoded_transaction,
                {
                    "encoding": "base64",
                    "sigVerify": sig_verify,
                    "replaceRecentBlockhash": replace_recent_blockhash,
                    "commitment": self.commitment,
                },
            ],
        )
        value = result.get("value")
        if not isinstance(value, dict):
            raise SolanaRpcError("Malformed simulation response")
        return SimulationResult(
            successful=value.get("err") is None,
            error=value.get("err"),
            logs=tuple(str(item) for item in value.get("logs") or []),
            units_consumed=(
                None
                if value.get("unitsConsumed") is None
                else int(value["unitsConsumed"])
            ),
            replacement_blockhash=value.get("replacementBlockhash"),
            accounts=tuple(value.get("accounts") or []),
            read_only=True,
            transaction_signed=False,
            transaction_submitted=False,
        )

    def send_transaction(self, *_args: Any, **_kwargs: Any) -> None:
        raise SigningDisabledError(
            "Transaction submission is disabled in G.24"
        )


__all__ = ["SolanaReadOnlyRpcClient", "TOKEN_PROGRAM_ID"]
