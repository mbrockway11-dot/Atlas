"""Keyless, read-only Hyperliquid client for the copy-trading tracker.

Two public endpoints, no authentication:

- ``GET  stats-data.hyperliquid.xyz/Mainnet/leaderboard`` -> leaderboard rows
- ``POST api.hyperliquid.xyz/info {"type": "clearinghouseState", ...}`` ->
  one wallet's open positions and margin summary

There is deliberately **no signing path and no order endpoint** in this client.
It can read public state; it cannot place, fund, or cancel an order. That is
the structural guarantee that the tracker is read-only, mirrored by the
provenance flags returned from :meth:`HyperliquidReadClient.provenance`.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from atlas.investment.hyper_copytrade.contracts import (
    LeaderboardEntry,
    WalletState,
)


LEADERBOARD_URL = "https://stats-data.hyperliquid.xyz/Mainnet/leaderboard"
INFO_URL = "https://api.hyperliquid.xyz/info"

DEFAULT_USER_AGENT = "Atlas-HyperCopytrade/1.0 (read-only)"
DEFAULT_TIMEOUT_SECONDS = 25.0
# The leaderboard is large (~40k rows, tens of MB); cap generously but bound it.
MAXIMUM_RESPONSE_BYTES = 64_000_000


class HyperliquidClientError(RuntimeError):
    """A read request to Hyperliquid failed or returned an unusable payload."""


class HyperliquidReadClient:
    """Read-only access to Hyperliquid public leaderboard and wallet state."""

    def __init__(
        self,
        *,
        leaderboard_url: str = LEADERBOARD_URL,
        info_url: str = INFO_URL,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        maximum_response_bytes: int = MAXIMUM_RESPONSE_BYTES,
    ) -> None:
        self.leaderboard_url = str(leaderboard_url)
        self.info_url = str(info_url)
        self.user_agent = str(user_agent).strip()
        self.timeout_seconds = float(timeout_seconds)
        self.maximum_response_bytes = max(1, int(maximum_response_bytes))

    def fetch_leaderboard(self) -> list[LeaderboardEntry]:
        """Fetch and normalize every leaderboard row.

        Rows that fail to parse (malformed address, non-finite metric) are
        skipped rather than aborting the whole fetch, matching the batch
        convention: one bad row must not lose the other 40,000.
        """
        payload = self._get_json(self.leaderboard_url)
        rows = payload.get("leaderboardRows") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise HyperliquidClientError(
                "Leaderboard payload missing 'leaderboardRows' list."
            )

        entries: list[LeaderboardEntry] = []
        for row in rows:
            try:
                entries.append(LeaderboardEntry.from_row(row))
            except (KeyError, ValueError, TypeError):
                continue
        if not entries:
            raise HyperliquidClientError("Leaderboard returned no usable rows.")
        return entries

    def fetch_wallet_state(self, address: str) -> WalletState:
        """Fetch one wallet's open perpetual positions and margin summary."""
        address = str(address).strip().lower()
        payload = self._post_json(
            self.info_url,
            {"type": "clearinghouseState", "user": address},
        )
        if not isinstance(payload, dict):
            raise HyperliquidClientError(
                f"clearinghouseState for {address} was not an object."
            )
        try:
            return WalletState.from_clearinghouse_state(address, payload)
        except (KeyError, ValueError, TypeError) as error:
            raise HyperliquidClientError(
                f"Could not parse wallet state for {address}: {error}"
            ) from error

    def fetch_user_fills(self, address: str) -> list[dict[str, Any]]:
        """Fetch a wallet's recent fills (up to ~2000), newest first.

        Each fill is the raw Hyperliquid record: ``coin``, ``px``, ``sz``,
        ``side`` (``B`` buy / ``A`` sell), ``time`` (ms), ``startPosition``,
        ``dir`` (``Open Long`` / ``Close Long`` / ``Open Short`` /
        ``Close Short`` / flips), ``closedPnl`` and ``fee``. Reconstruction
        into round-trip trades happens in ``trade_reconstruction.py``; this
        method only fetches and shape-checks.
        """
        address = str(address).strip().lower()
        payload = self._post_json(
            self.info_url,
            {"type": "userFills", "user": address},
        )
        if not isinstance(payload, list):
            raise HyperliquidClientError(
                f"userFills for {address} was not a list."
            )
        return payload

    def fetch_user_fills_by_time(
        self,
        address: str,
        start_time_ms: int,
        end_time_ms: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch fills in ``[start_time_ms, end_time_ms]``, oldest first (<=2000)."""
        address = str(address).strip().lower()
        body: dict[str, Any] = {
            "type": "userFillsByTime",
            "user": address,
            "startTime": int(start_time_ms),
        }
        if end_time_ms is not None:
            body["endTime"] = int(end_time_ms)
        payload = self._post_json(self.info_url, body)
        if not isinstance(payload, list):
            raise HyperliquidClientError(
                f"userFillsByTime for {address} was not a list."
            )
        return payload

    def fetch_full_fill_history(
        self,
        address: str,
        start_time_ms: int,
        *,
        maximum_pages: int = 20,
    ) -> list[dict[str, Any]]:
        """Page forward from ``start_time_ms`` to present, recovering full history.

        The time-windowed endpoint returns at most 2000 fills, oldest-first, so
        a single page truncates an active trader's history and leaves round
        trips unclosed. This walks forward -- advancing the cursor past the
        newest fill of each full page -- until a short page signals the present
        is reached or ``maximum_pages`` is hit. Fills are de-duplicated by
        trade id (``tid``), since page boundaries can overlap. If the page cap
        is reached the returned history is partial; callers should note it.
        """
        address = str(address).strip().lower()
        collected: list[dict[str, Any]] = []
        seen: set[Any] = set()
        cursor = int(start_time_ms)

        for _ in range(max(1, int(maximum_pages))):
            page = self.fetch_user_fills_by_time(address, cursor)
            if not page:
                break
            for fill in page:
                tid = fill.get("tid")
                if tid in seen:
                    continue
                seen.add(tid)
                collected.append(fill)
            if len(page) < 2000:
                break  # caught up to the present
            cursor = max(int(fill["time"]) for fill in page) + 1

        return collected

    def fetch_candles(
        self,
        coin: str,
        interval: str,
        start_time_ms: int,
        end_time_ms: int,
    ) -> list[dict[str, Any]]:
        """Fetch OHLCV candles for a coin over a time range (<=5000 candles).

        Each candle: ``t`` (open ms), ``T`` (close ms), ``o``/``h``/``l``/``c``
        (prices), ``v`` (volume), ``n`` (trades). Used to place a trade's entry
        within its coin's recent high/low range.
        """
        coin = str(coin).strip().upper()
        payload = self._post_json(
            self.info_url,
            {
                "type": "candleSnapshot",
                "req": {
                    "coin": coin,
                    "interval": str(interval),
                    "startTime": int(start_time_ms),
                    "endTime": int(end_time_ms),
                },
            },
        )
        if not isinstance(payload, list):
            raise HyperliquidClientError(
                f"candleSnapshot for {coin} was not a list."
            )
        return payload

    def provenance(self) -> dict[str, Any]:
        """Return the read-only provenance flags for artifacts and logs."""
        return {
            "source": "hyperliquid",
            "leaderboard_url": self.leaderboard_url,
            "info_url": self.info_url,
            "read_only": True,
            "credentials_used": False,
            "signing_available": False,
            "live_execution": False,
            "paper_only": True,
        }

    def _get_json(self, url: str) -> Any:
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": self.user_agent},
            method="GET",
        )
        return self._read_json(request, url)

    def _post_json(self, url: str, body: dict[str, Any]) -> Any:
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": self.user_agent,
            },
            method="POST",
        )
        return self._read_json(request, url)

    def _read_json(self, request: urllib.request.Request, url: str) -> Any:
        try:
            with urllib.request.urlopen(
                request, timeout=self.timeout_seconds
            ) as response:
                raw = response.read(self.maximum_response_bytes + 1)
        except urllib.error.HTTPError as error:
            raise HyperliquidClientError(
                f"HTTP {error.code} from {url}."
            ) from error
        except urllib.error.URLError as error:
            raise HyperliquidClientError(
                f"Network error contacting {url}: {error.reason}"
            ) from error
        except TimeoutError as error:
            raise HyperliquidClientError(f"Timed out contacting {url}.") from error

        if len(raw) > self.maximum_response_bytes:
            raise HyperliquidClientError(f"Response from {url} exceeded cap.")

        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise HyperliquidClientError(
                f"Invalid JSON from {url}: {error}"
            ) from error
