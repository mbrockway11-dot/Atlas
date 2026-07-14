from __future__ import annotations

from pathlib import Path

import pytest

from atlas.investment.solana import (
    FixtureJsonTransport,
    ReadOnlyWalletService,
    SigningDisabledError,
    SolanaReadOnlyRpcClient,
    WalletRegistration,
)


PUBLIC_KEY = "83astBRguLMdt2h5U1Tpdq5tjFoJ6noeGwaY3mDLVcri"


def test_wallet_service_captures_read_only_snapshot(tmp_path: Path) -> None:
    transport = FixtureJsonTransport(
        post_responses=[
            {
                "result": {"context": {"slot": 1}, "value": 1000000000}
            },
            {
                "result": {"context": {"slot": 1}, "value": []}
            },
        ]
    )
    service = ReadOnlyWalletService(
        registration=WalletRegistration(
            wallet_id="wallet",
            public_key=PUBLIC_KEY,
            label="test",
        ),
        rpc=SolanaReadOnlyRpcClient(
            rpc_url="https://example.invalid",
            transport=transport,
        ),
        output_dir=tmp_path,
    )

    snapshot = service.capture_snapshot()

    assert snapshot.native_balance.sol == 1.0
    assert snapshot.read_only is True
    assert snapshot.signing_enabled is False
    assert snapshot.submission_enabled is False
    assert (tmp_path / "latest_wallet_snapshot.json").exists()

    with pytest.raises(SigningDisabledError):
        service.sign_transaction()
