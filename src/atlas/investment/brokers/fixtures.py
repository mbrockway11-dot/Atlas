"""Deterministic recorded-fixture transport for G.19 broker tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .generic_rest_paper import (
    RestRateLimitError,
    RestTransportError,
)


class FixtureRestTransport:
    """Replay predefined responses without network access."""

    def __init__(
        self,
        fixtures: Mapping[tuple[str, str], list[Mapping[str, Any]] | Mapping[str, Any]],
    ) -> None:
        self._fixtures: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
        for key, value in fixtures.items():
            if isinstance(value, Mapping):
                self._fixtures[(key[0].upper(), key[1])] = [deepcopy(value)]
            else:
                self._fixtures[(key[0].upper(), key[1])] = [
                    deepcopy(item) for item in value
                ]
        self.requests: list[dict[str, Any]] = []

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any]:
        key = (method.upper(), path)
        self.requests.append(
            {
                "method": method.upper(),
                "path": path,
                "json_body": None if json_body is None else dict(json_body),
                "headers": None if headers is None else dict(headers),
            }
        )

        queue = self._fixtures.get(key)
        if not queue:
            raise RestTransportError(f"No fixture registered for {method} {path}")

        payload = queue.pop(0)
        if payload.get("__raise__") == "rate_limit":
            raise RestRateLimitError(str(payload.get("message", "rate limited")))
        if payload.get("__raise__") == "transport":
            raise RestTransportError(str(payload.get("message", "transport failure")))
        return deepcopy(payload)


__all__ = ["FixtureRestTransport"]
