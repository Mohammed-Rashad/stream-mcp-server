"""Stream MCP server — FastMCP application entry-point.

This module is intentionally thin: it wires together configuration,
the HTTP client, and all tool/resource registrations.

Two modes of operation:

* **Local (stdio)** — ``stream-mcp`` command.  Uses ``STREAM_API_KEY`` env var.
* **Remote (SSE)** — ``stream-mcp-remote`` command.  Each user passes their
  own API key as a ``Bearer`` token; the server is stateless.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from stream_mcp.client import StreamClient
from stream_mcp.config import settings
from stream_mcp.tools import register_all_tools

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Create a shared :class:`StreamClient` when an API key is configured.

    In **local mode** (``STREAM_API_KEY`` set), a single client is shared
    across all tool calls.  In **remote mode** (no env key), the lifespan
    yields an empty context and per-user clients are created on-the-fly
    by :func:`~stream_mcp.helpers.get_client`.
    """
    if settings.stream_api_key:
        # Local mode — shared client
        client = StreamClient(
            api_key=settings.stream_api_key,
            base_url=settings.stream_base_url,
            timeout=settings.stream_timeout,
            max_retries=settings.stream_max_retries,
        )
        async with client:
            logger.info("StreamClient ready → %s", settings.stream_base_url)
            yield {"client": client}
        logger.info("StreamClient closed.")
    else:
        # Remote mode — no shared client; each user provides their own key
        logger.info("Remote mode — no STREAM_API_KEY set; users must provide Bearer tokens.")
        yield {}


mcp = FastMCP(
    name="stream-mcp",
    instructions=(
        "MCP server for Stream (streampay.sa) — "
        "payment links, customers, products, coupons, invoices, payments."
    ),
    lifespan=lifespan,
)

# Register all tools & resources onto the FastMCP instance
register_all_tools(mcp)


# ── CLI entry-points ──────────────────────────────────────────────────

def main() -> None:
    """CLI entry-point for **local** mode (``stream-mcp`` command, stdio transport)."""
    mcp.run()


def main_remote() -> None:
    """CLI entry-point for **remote** mode (``stream-mcp-remote`` command).

    Starts the MCP server over SSE with Bearer-token authentication.
    Each user passes their own Stream API key in the ``Authorization`` header.

    Environment variables:

    * ``HOST`` — bind address (default ``0.0.0.0``)
    * ``PORT`` — bind port   (default ``8000``)
    """
    import uvicorn

    from stream_mcp.auth import BearerAuthMiddleware

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))

    # Get the ASGI app from FastMCP and wrap with auth middleware
    app = mcp.http_app(transport="streamable-http")
    app = BearerAuthMiddleware(app)

    logger.info("Starting remote MCP server on %s:%d (streamable-http + Bearer auth)", host, port)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
