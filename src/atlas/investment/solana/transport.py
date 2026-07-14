"""Injected HTTP transports for Atlas G.24."""

from __future__ import annotations

import json
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .errors import JupiterApiError, SolanaRpcError


class JsonTransport(Protocol):
    def post_json(
        self,
        url: str,
        payload: Mapping[str, Any],
        *,
        headers: Mapping[str, str] | None = None,
        timeout: float = 15.0,
    ) -> Mapping[str, Any]: ...

    def get_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        timeout: float = 15.0,
    ) -> Mapping[str, Any]: ...


class UrllibJsonTransport:
    def post_json(
        self,
        url: str,
        payload: Mapping[str, Any],
        *,
        headers: Mapping[str, str] | None = None,
        timeout: float = 15.0,
    ) -> Mapping[str, Any]:
        request_headers = {"Content-Type": "application/json"}
        request_headers.update(dict(headers or {}))
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=request_headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                value = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise SolanaRpcError(str(exc)) from exc
        if not isinstance(value, dict):
            raise SolanaRpcError("RPC response must be a JSON object")
        return value

    def get_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        timeout: float = 15.0,
    ) -> Mapping[str, Any]:
        request = Request(url, headers=dict(headers or {}), method="GET")
        try:
            with urlopen(request, timeout=timeout) as response:
                value = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise JupiterApiError(str(exc)) from exc
        if not isinstance(value, dict):
            raise JupiterApiError("Jupiter response must be a JSON object")
        return value


class FixtureJsonTransport:
    def __init__(
        self,
        *,
        post_responses: list[Mapping[str, Any]] | None = None,
        get_responses: list[Mapping[str, Any]] | None = None,
    ) -> None:
        self.post_responses = [dict(item) for item in (post_responses or [])]
        self.get_responses = [dict(item) for item in (get_responses or [])]
        self.requests: list[dict[str, Any]] = []

    def post_json(
        self,
        url: str,
        payload: Mapping[str, Any],
        *,
        headers: Mapping[str, str] | None = None,
        timeout: float = 15.0,
    ) -> Mapping[str, Any]:
        self.requests.append(
            {
                "method": "POST",
                "url": url,
                "payload": dict(payload),
                "headers": dict(headers or {}),
            }
        )
        if not self.post_responses:
            raise SolanaRpcError("No POST fixture response remains")
        return self.post_responses.pop(0)

    def get_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        timeout: float = 15.0,
    ) -> Mapping[str, Any]:
        self.requests.append(
            {
                "method": "GET",
                "url": url,
                "headers": dict(headers or {}),
            }
        )
        if not self.get_responses:
            raise JupiterApiError("No GET fixture response remains")
        return self.get_responses.pop(0)


__all__ = ["FixtureJsonTransport", "JsonTransport", "UrllibJsonTransport"]
