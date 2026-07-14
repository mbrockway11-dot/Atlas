"""Read-only Jupiter quote client for Atlas G.24."""

from __future__ import annotations

from urllib.parse import urlencode

from .contracts import JupiterQuote, JupiterQuoteRequest
from .errors import JupiterApiKeyRequired, JupiterApiError, SigningDisabledError
from .transport import JsonTransport, UrllibJsonTransport
from .validation import validate_public_key


class JupiterReadOnlyClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "https://api.jup.ag/swap/v1",
        transport: JsonTransport | None = None,
    ) -> None:
        self.api_key = api_key.strip() if api_key else ""
        self.base_url = base_url.rstrip("/")
        self.transport = transport or UrllibJsonTransport()

    def get_quote(self, request: JupiterQuoteRequest) -> JupiterQuote:
        if not self.api_key:
            raise JupiterApiKeyRequired(
                "Jupiter production quote API requires x-api-key; "
                "wallet monitoring remains available without it"
            )
        validate_public_key(request.input_mint)
        validate_public_key(request.output_mint)
        if request.amount <= 0:
            raise JupiterApiError("Quote amount must be positive")
        if not 0 <= request.slippage_bps <= 10_000:
            raise JupiterApiError("slippage_bps is outside the valid range")
        if request.swap_mode not in {"ExactIn", "ExactOut"}:
            raise JupiterApiError("swap_mode must be ExactIn or ExactOut")

        query = urlencode(
            {
                "inputMint": request.input_mint,
                "outputMint": request.output_mint,
                "amount": request.amount,
                "slippageBps": request.slippage_bps,
                "swapMode": request.swap_mode,
                "onlyDirectRoutes": str(request.only_direct_routes).lower(),
            }
        )
        payload = self.transport.get_json(
            f"{self.base_url}/quote?{query}",
            headers={"x-api-key": self.api_key},
        )
        if payload.get("error"):
            raise JupiterApiError(str(payload["error"]))
        try:
            return JupiterQuote(
                input_mint=str(payload["inputMint"]),
                output_mint=str(payload["outputMint"]),
                in_amount=str(payload["inAmount"]),
                out_amount=str(payload["outAmount"]),
                other_amount_threshold=str(payload["otherAmountThreshold"]),
                swap_mode=str(payload["swapMode"]),
                slippage_bps=int(payload["slippageBps"]),
                price_impact_pct=str(payload["priceImpactPct"]),
                context_slot=int(payload["contextSlot"]),
                time_taken=float(payload["timeTaken"]),
                route_plan=tuple(payload.get("routePlan") or []),
                read_only=True,
                transaction_built=False,
                transaction_signed=False,
                transaction_submitted=False,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise JupiterApiError("Malformed Jupiter quote payload") from exc

    def build_transaction(self, *_args, **_kwargs) -> None:
        raise SigningDisabledError(
            "Transaction construction is disabled until G.25"
        )

    def execute_transaction(self, *_args, **_kwargs) -> None:
        raise SigningDisabledError(
            "Jupiter execution is disabled in G.24"
        )


__all__ = ["JupiterReadOnlyClient"]
