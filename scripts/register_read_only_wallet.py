"""Register a Phantom/Solana public key for read-only Atlas monitoring."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from atlas.investment.solana import (
    SolanaValidationError,
    WalletRegistration,
    validate_network,
    validate_public_key,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-key", required=True)
    parser.add_argument("--wallet-id", default="atlas-phantom")
    parser.add_argument("--label", default="Atlas Phantom Wallet")
    parser.add_argument("--network", default="mainnet-beta")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/solana_wallet/wallet_registration.json"),
    )
    args = parser.parse_args()

    try:
        registration = WalletRegistration(
            wallet_id=args.wallet_id,
            public_key=validate_public_key(args.public_key),
            label=args.label,
            network=validate_network(args.network),
            read_only=True,
            signing_enabled=False,
            submission_enabled=False,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(asdict(registration), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, SolanaValidationError, ValueError) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 2

    print(json.dumps({"success": True, "wallet": asdict(registration)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
