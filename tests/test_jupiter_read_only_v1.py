from __future__ import annotations

import pytest

from atlas.investment.solana import (
    FixtureJsonTransport,
    JupiterApiKeyRequired,
    JupiterQuoteRequest,
    JupiterReadOnlyClient,
    SigningDisabledError,
)


SOL_MINT = "So11111111111111111111111111111111111111112"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def test_api_key_is_required_for_current_production_quote_api() -> None:
    client = JupiterReadOnlyClient(transport=FixtureJsonTransport())

    with pytest.raises(JupiterApiKeyRequired):
        client.get_quote(
            JupiterQuoteRequest(
                input_mint=SOL_MINT,
                output_mint=USDC_MINT,
                amount=100000000,
            )
        )


def test_quote_is_read_only_and_normalized() -> None:
    transport = FixtureJsonTransport(
        get_responses=[
            {
                "inputMint": SOL_MINT,
                "outputMint": USDC_MINT,
                "inAmount": "100000000",
                "outAmount": "17057460",
                "otherAmountThreshold": "16886885",
                "swapMode": "ExactIn",
                "slippageBps": 100,
                "priceImpactPct": "0.0001",
                "routePlan": [],
                "contextSlot": 324307186,
                "timeTaken": 0.012,
            }
        ]
    )
    client = JupiterReadOnlyClient(api_key="fixture-key", transport=transport)
    quote = client.get_quote(
        JupiterQuoteRequest(
            input_mint=SOL_MINT,
            output_mint=USDC_MINT,
            amount=100000000,
            slippage_bps=100,
        )
    )

    assert quote.read_only is True
    assert quote.transaction_built is False
    assert quote.transaction_signed is False
    assert quote.transaction_submitted is False
    assert transport.requests[0]["headers"]["x-api-key"] == "fixture-key"


def test_transaction_build_and_execution_are_disabled() -> None:
    client = JupiterReadOnlyClient(api_key="fixture")

    with pytest.raises(SigningDisabledError):
        client.build_transaction()
    with pytest.raises(SigningDisabledError):
        client.execute_transaction()
