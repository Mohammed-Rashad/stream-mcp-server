"""Thin async HTTP client wrapper for the Stream API.

All auth, retry, and error-handling logic lives here — zero duplication across tools.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class StreamError(Exception):
    """Base exception for all Stream-related errors."""


class StreamAPIError(StreamError):
    """Raised when the Stream API returns a non-2xx response."""

    def __init__(self, message: str, status_code: int, body: dict[str, Any]) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(message)


class StreamAuthError(StreamAPIError):
    """401 / 403 — authentication or authorisation failure."""


class StreamNotFoundError(StreamAPIError):
    """404 — requested resource does not exist."""


class StreamValidationError(StreamAPIError):
    """422 — request payload failed server-side validation."""


class StreamRateLimitError(StreamAPIError):
    """429 — rate-limit exceeded."""


# ---------------------------------------------------------------------------
# Mapping status codes → specific exception classes
# ---------------------------------------------------------------------------
_STATUS_EXCEPTION_MAP: dict[int, type[StreamAPIError]] = {
    401: StreamAuthError,
    403: StreamAuthError,
    404: StreamNotFoundError,
    422: StreamValidationError,
    429: StreamRateLimitError,
}

# Status codes eligible for automatic retry
_RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class StreamClient:
    """Async HTTP client for the Stream API.

    * Injects ``x-api-key`` on every request.
    * Exponential-backoff retry for 429 / 5xx (up to *max_retries*).
    * Raises :class:`StreamAPIError` (or a subclass) on non-2xx responses.

    Usage::

        client = StreamClient(api_key="...", base_url="...", timeout=30)
        async with client:
            data = await client.get("/v2/customers")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 2,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._http: httpx.AsyncClient | None = None

    # -- context manager ------------------------------------------------------

    async def __aenter__(self) -> "StreamClient":
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "x-api-key": self._api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(self._timeout),
        )
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._http:
            await self._http.aclose()
            self._http = None

    # -- public helpers -------------------------------------------------------

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http is None:
            raise StreamError("StreamClient is not open. Use `async with client:` …")
        return self._http

    # -- convenience verbs ----------------------------------------------------

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("POST", path, json=body)

    async def put(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("PUT", path, json=body)

    async def patch(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("PATCH", path, json=body)

    async def delete(self, path: str) -> dict[str, Any]:
        return await self._request("DELETE", path)

    # -- internal request engine ----------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute *method* against *path* with retry logic."""

        last_exc: StreamAPIError | None = None

        for attempt in range(1 + self._max_retries):
            if attempt > 0:
                delay = 2 ** attempt  # exponential back-off: 2, 4, 8 …
                logger.info(
                    "Retrying %s %s (attempt %d/%d) in %ds …",
                    method, path, attempt + 1, 1 + self._max_retries, delay,
                )
                await asyncio.sleep(delay)

            try:
                response = await self.http.request(
                    method,
                    path,
                    params=params,
                    json=json,
                )
            except httpx.HTTPError as exc:
                logger.error("HTTP transport error on %s %s: %s", method, path, exc)
                raise StreamError(f"Transport error: {exc}") from exc

            if response.is_success:
                try:
                    return response.json()
                except ValueError:
                    # Some endpoints may return empty bodies on success (e.g. 204)
                    return {}

            # -- non-2xx handling --
            status = response.status_code
            try:
                body = response.json()
            except ValueError:
                body = {"raw": response.text}

            message = body.get("message") or body.get("error") or response.reason_phrase or "Unknown error"
            exc_cls = _STATUS_EXCEPTION_MAP.get(status, StreamAPIError)
            last_exc = exc_cls(message=str(message), status_code=status, body=body)

            if status in _RETRYABLE_STATUS_CODES and attempt < self._max_retries:
                logger.warning(
                    "Retryable %d on %s %s: %s", status, method, path, message,
                )
                continue

            raise last_exc

        # Should never be reached, but just in case:
        assert last_exc is not None
        raise last_exc
