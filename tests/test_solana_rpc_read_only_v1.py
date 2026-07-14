from __future__ import annotations

from atlas.investment.solana import (
    FixtureJsonTransport,
    SolanaReadOnlyRpcClient,
)


PUBLIC_KEY = "83astBRguLMdt2h5U1Tpdq5tjFoJ6noeGwaY3mDLVcri"


def test_native_and_token_balance_normalization() -> None:
    transport = FixtureJsonTransport(
        post_responses=[
            {
                "jsonrpc": "2.0",
                "result": {"context": {"slot": 10}, "value": 2_000_000_000},
                "id": 1,
            },
            {
                "jsonrpc": "2.0",
                "result": {
                    "context": {"slot": 11},
                    "value": [
                        {
                            "pubkey": "BGocb4GEpbTFm8UFV2VsDSaBXHELPfAXrvd4vtt8QWrA",
                            "account": {
                                "data": {
                                    "parsed": {
                                        "info": {
                                            "mint": PUBLIC_KEY,
                                            "owner": PUBLIC_KEY,
                                            "state": "initialized",
                                            "tokenAmount": {
                                                "amount": "1000000",
                                                "decimals": 6,
                                                "uiAmount": 1.0,
                                            },
                                        }
                                    }
                                }
                            },
                        }
                    ],
                },
                "id": 2,
            },
        ]
    )
    client = SolanaReadOnlyRpcClient(
        rpc_url="https://example.invalid",
        transport=transport,
    )

    native = client.get_native_balance(PUBLIC_KEY)
    tokens = client.get_token_balances(PUBLIC_KEY)

    assert native.sol == 2.0
    assert tokens[0].ui_amount == 1.0
    assert all(request["method"] == "POST" for request in transport.requests)
