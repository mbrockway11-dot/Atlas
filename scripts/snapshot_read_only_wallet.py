"""Capture SOL and SPL-token balances for a registered wallet."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from atlas.investment.solana import (
    ReadOnlyWalletService,
    SolanaIntegrationError,
    SolanaReadOnlyRpcClient,
    WalletRegistration,
    rpc_url_for_network,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registration",
        type=Path,
        default=Path("output/solana_wallet/wallet_registration.json"),
    )
    parser.add_argument("--rpc-url", default="")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/solana_wallet"),
    )
    args = parser.parse_args()

    try:
        payload = json.loads(args.registration.read_text(encoding="utf-8-sig"))
        registration = WalletRegistration(**payload)
        rpc = SolanaReadOnlyRpcClient(
            rpc_url=args.rpc_url or rpc_url_for_network(registration.network)
        )
        snapshot = ReadOnlyWalletService(
            registration=registration,
            rpc=rpc,
            output_dir=args.output_dir,
        ).capture_snapshot()
    except (
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
        SolanaIntegrationError,
    ) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 2

    print(json.dumps({"success": True, "snapshot": asdict(snapshot)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
