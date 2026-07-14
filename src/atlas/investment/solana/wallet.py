"""Read-only wallet registration and snapshot service for Atlas G.24."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path

from .contracts import WalletRegistration, WalletSnapshot
from .errors import SigningDisabledError
from .rpc import SolanaReadOnlyRpcClient
from .validation import validate_network, validate_public_key


def _canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash(value) -> str:
    material = dict(value)
    material.pop("record_hash", None)
    return hashlib.sha256(_canonical(material).encode("utf-8")).hexdigest()


class ReadOnlyWalletService:
    def __init__(
        self,
        *,
        registration: WalletRegistration,
        rpc: SolanaReadOnlyRpcClient,
        output_dir: Path,
    ) -> None:
        validate_public_key(registration.public_key)
        validate_network(registration.network)
        if not registration.read_only:
            raise ValueError("G.24 wallet registration must be read-only")
        if registration.signing_enabled or registration.submission_enabled:
            raise ValueError("Signing and submission must remain disabled")
        self.registration = registration
        self.rpc = rpc
        self.output_dir = output_dir

    def capture_snapshot(self) -> WalletSnapshot:
        native = self.rpc.get_native_balance(self.registration.public_key)
        tokens = self.rpc.get_token_balances(self.registration.public_key)
        previous_hash = ""
        history_path = self.output_dir / "wallet_history.jsonl"
        if history_path.exists():
            lines = [
                json.loads(line)
                for line in history_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            if lines:
                previous_hash = str(lines[-1]["record_hash"])

        snapshot = WalletSnapshot(
            wallet=self.registration,
            native_balance=native,
            token_balances=tokens,
            captured_at=datetime.now(timezone.utc).isoformat(),
            previous_record_hash=previous_hash,
            read_only=True,
            signing_enabled=False,
            submission_enabled=False,
        )
        payload = asdict(snapshot)
        payload["record_hash"] = _hash(payload)
        snapshot = replace(snapshot, record_hash=payload["record_hash"])

        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "latest_wallet_snapshot.json").write_text(
            json.dumps(asdict(snapshot), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with history_path.open("a", encoding="utf-8") as handle:
            handle.write(_canonical(asdict(snapshot)) + "\n")
        return snapshot

    def sign_transaction(self, *_args, **_kwargs) -> None:
        raise SigningDisabledError("Phantom signing begins in G.25")


__all__ = ["ReadOnlyWalletService"]
