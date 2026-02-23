"""Shared helpers for tool handlers.

The main entry-point is :func:`get_client` which returns a
:class:`~stream_mcp.client.StreamClient` for the current request.

* **Local mode** (stdio) → returns the shared client from ``lifespan_context``.
* **Remote mode** (SSE / streamable-http) → creates (and caches) a per-user
  client using the Bearer token (and optional base-URL override) extracted
  by :class:`~stream_mcp.auth.BearerAuthMiddleware`.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from stream_mcp.auth import current_api_key, current_base_url
from stream_mcp.client import StreamClient, StreamError
from stream_mcp.config import settings

if TYPE_CHECKING:
    from fastmcp.server.context import Context

logger = logging.getLogger(__name__)

# Cache of per-user clients (remote mode).
# Key = "<api_key>::<base_url>" so different base URLs get separate clients.
_client_cache: dict[str, StreamClient] = {}


async def get_client(ctx: "Context") -> StreamClient:
    """Return a :class:`StreamClient` for the current request.

    Resolution order:

    1. **Lifespan client** — used in local / stdio mode where a single
       ``STREAM_API_KEY`` is set as an environment variable.
    2. **Per-user client** — used in remote mode where each user passes
       their own API key as a Bearer token and (optionally) a custom
       base URL via the ``X-Stream-Base-URL`` header.
    """
    # ── 1. Local mode: shared client from server lifespan ─────────────
    shared_client = ctx.lifespan_context.get("client")
    if shared_client is not None:
        return shared_client

    # ── 2. Remote mode: per-user client from Bearer token ─────────────
    api_key = current_api_key.get()
    if not api_key:
        raise StreamError(
            "No Stream API key found. "
            "In local mode, set the STREAM_API_KEY env var. "
            "In remote mode, pass your key as a Bearer token in the Authorization header."
        )

    base_url = current_base_url.get() or settings.stream_base_url
    cache_key = f"{api_key}::{base_url}"

    if cache_key not in _client_cache:
        client = StreamClient(
            api_key=api_key,
            base_url=base_url,
            timeout=settings.stream_timeout,
            max_retries=settings.stream_max_retries,
        )
        await client.__aenter__()
        _client_cache[cache_key] = client
        logger.info(
            "Created cached StreamClient for remote user (key=…%s, base=%s)",
            api_key[-4:], base_url,
        )

    return _client_cache[cache_key]
