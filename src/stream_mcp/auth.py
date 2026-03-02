"""Authentication middleware for the remote (SSE / Streamable HTTP) MCP server.

Each connecting user passes their **own** Stream API key as a Bearer token
in the ``Authorization`` header.

An ASGI middleware extracts the token and stores it in a :mod:`contextvars`
variable so that tool handlers can read it without any changes to FastMCP internals.

Flow::

    Client → Authorization: Bearer sk_live_xxx
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


# ── pure ASGI middleware (works with SSE + streaming responses) ───────
class BearerAuthMiddleware:
    """Extract Bearer token from Authorization header and store in context variables.

    Supported headers:

    * ``Authorization: Bearer <key>`` → Stream API key  (**required**)

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

        await self.app(scope, receive, send)
