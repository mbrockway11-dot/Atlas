"""Minimal provider-neutral HTTP transport for Atlas market-data adapters."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class HttpJsonResponse:
    """Normalized JSON HTTP response."""

    status_code: int
    payload: Any
    headers: Mapping[
        str,
        str,
    ]
    elapsed_ms: float
    url: str


class JsonHttpTransport(
    Protocol
):
    """Injectable transport contract used by network providers."""

    def get_json(
        self,
        url: str,
        *,
        query: Mapping[
            str,
            object,
        ] | None = None,
        headers: Mapping[
            str,
            str,
        ] | None = None,
        timeout_seconds: float = 10.0,
    ) -> HttpJsonResponse:
        ...


class UrllibJsonTransport:
    """Standard-library JSON transport with no authentication behavior."""

    def __init__(
        self,
        *,
        user_agent: str = (
            "Atlas-Market-Data/1.0"
        ),
        maximum_response_bytes: int = (
            5_000_000
        ),
    ) -> None:
        self.user_agent = str(
            user_agent
        ).strip()

        self.maximum_response_bytes = max(
            1,
            int(
                maximum_response_bytes
            ),
        )

    def get_json(
        self,
        url: str,
        *,
        query: Mapping[
            str,
            object,
        ] | None = None,
        headers: Mapping[
            str,
            str,
        ] | None = None,
        timeout_seconds: float = 10.0,
    ) -> HttpJsonResponse:
        final_url = build_url(
            url,
            query=query,
        )

        request_headers = {
            "Accept": (
                "application/json"
            ),
            "User-Agent": (
                self.user_agent
            ),
        }

        for key, value in (
            headers or {}
        ).items():
            request_headers[
                str(key)
            ] = str(value)

        request = urllib.request.Request(
            final_url,
            headers=request_headers,
            method="GET",
        )

        started = time.perf_counter()

        try:
            with urllib.request.urlopen(
                request,
                timeout=float(
                    timeout_seconds
                ),
            ) as response:
                raw = response.read(
                    self.maximum_response_bytes
                    + 1
                )

                if len(raw) > (
                    self.maximum_response_bytes
                ):
                    raise RuntimeError(
                        "HTTP_RESPONSE_TOO_LARGE"
                    )

                status_code = int(
                    response.status
                )

                response_headers = {
                    str(key): str(value)
                    for key, value
                    in response.headers.items()
                }

        except urllib.error.HTTPError as error:
            raw = error.read(
                self.maximum_response_bytes
            )

            message = decode_error_body(
                raw
            )

            raise RuntimeError(
                "HTTP_STATUS_ERROR:"
                + str(error.code)
                + ":"
                + message
            ) from error

        except urllib.error.URLError as error:
            raise RuntimeError(
                "HTTP_NETWORK_ERROR:"
                + str(error.reason)
            ) from error

        except TimeoutError as error:
            raise RuntimeError(
                "HTTP_TIMEOUT"
            ) from error

        elapsed_ms = (
            time.perf_counter()
            - started
        ) * 1_000.0

        try:
            payload = json.loads(
                raw.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as error:
            raise RuntimeError(
                "HTTP_JSON_INVALID"
            ) from error

        return HttpJsonResponse(
            status_code=status_code,
            payload=payload,
            headers=response_headers,
            elapsed_ms=elapsed_ms,
            url=final_url,
        )


def build_url(
    url: str,
    *,
    query: Mapping[
        str,
        object,
    ] | None = None,
) -> str:
    if not query:
        return str(url)

    values = {
        str(key): str(value)
        for key, value
        in query.items()
        if value is not None
    }

    encoded = urllib.parse.urlencode(
        values
    )

    separator = (
        "&"
        if "?" in url
        else "?"
    )

    return (
        str(url)
        + separator
        + encoded
    )


def decode_error_body(
    raw: bytes,
) -> str:
    try:
        payload = json.loads(
            raw.decode("utf-8")
        )
    except Exception:
        return raw.decode(
            "utf-8",
            errors="replace",
        )[:500]

    if isinstance(
        payload,
        dict,
    ):
        for key in (
            "message",
            "error",
            "reason",
        ):
            value = payload.get(
                key
            )

            if value:
                return str(value)

    return str(payload)[:500]


__all__ = [
    "HttpJsonResponse",
    "JsonHttpTransport",
    "UrllibJsonTransport",
    "build_url",
]
