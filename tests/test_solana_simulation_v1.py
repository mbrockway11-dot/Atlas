from __future__ import annotations

import pytest

from atlas.investment.solana import (
    FixtureJsonTransport,
    SigningDisabledError,
    SolanaReadOnlyRpcClient,
)


def test_unsigned_transaction_simulation_is_normalized() -> None:
    transport = FixtureJsonTransport(
        post_responses=[
            {
                "result": {
                    "context": {"slot": 1},
                    "value": {
                        "err": None,
                        "logs": ["Program log: ok"],
                        "unitsConsumed": 1234,
                        "accounts": None,
                        "replacementBlockhash": {
                            "blockhash": "fixture",
                            "lastValidBlockHeight": 5,
                        },
                    },
                }
            }
        ]
    )
    client = SolanaReadOnlyRpcClient(
        rpc_url="https://example.invalid",
        transport=transport,
    )

    result = client.simulate_unsigned_transaction("ZmFrZQ==")

    assert result.successful is True
    assert result.units_consumed == 1234
    assert result.transaction_signed is False
    assert result.transaction_submitted is False

    with pytest.raises(SigningDisabledError):
        client.send_transaction("anything")
