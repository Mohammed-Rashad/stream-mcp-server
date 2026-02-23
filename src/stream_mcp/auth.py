"""Authentication middleware for the remote (SSE / Streamable HTTP) MCP server.

Each connecting user passes their **own** Stream API key as a Bearer token
in the ``Authorization`` header.  Optionally, a custom base URL can be
provided via the ``X-Stream-Base-URL`` header.

An ASGI middleware extracts both values and stores them in
:mod:`contextvars` variables so that tool handlers can read them
without any changes to FastMCP internals.

Flow::

    Client → Authorization: Bearer sk_live_xxx
           → X-Stream-Base-URL: https://custom-api.example.com  (optional)
           → ASGI middleware sets contextvars
           → FastMCP handles the MCP message
           → tool handler calls ``get_client(ctx)``
           → helper reads contextvars and returns a per-user StreamClient
"""

from __future__ import annotations

import contextvars
import logging

logger = logging.getLogger(__name__)

# ── per-request context variables ─────────────────────────────────────
current_api_key: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_api_key", default=None,
)
current_base_url: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_base_url", default=None,
)


# ── pure ASGI middleware (works with SSE + streaming responses) ───────
class BearerAuthMiddleware:
    """Extract auth and config headers, store in context variables.

    Supported headers:

    * ``Authorization: Bearer <key>`` → Stream API key  (**required**)
    * ``X-Stream-Base-URL: <url>``    → custom API base URL (optional)

    This is a thin, pure-ASGI middleware — it does **not** buffer the
    response, so it is safe to use with SSE / streaming transports.
    """

    def __init__(self, app):  # noqa: ANN001
        self.app = app

    async def __call__(self, scope, receive, send):  # noqa: ANN001
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))

            # ── API key (required) ────────────────────────────────────
            auth_header = headers.get(b"authorization", b"").decode()
            if auth_header.lower().startswith("bearer "):
                token = auth_header[7:].strip()
                current_api_key.set(token)
                logger.debug("Bearer token set for request (key=…%s)", token[-4:])

            # ── Base URL override (optional) ──────────────────────────
            base_url = headers.get(b"x-stream-base-url", b"").decode().strip()
            if base_url:
                current_base_url.set(base_url.rstrip("/"))
                logger.debug("Custom base URL set: %s", base_url)

        await self.app(scope, receive, send)
