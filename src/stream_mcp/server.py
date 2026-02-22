"""Stream MCP server — FastMCP application entry-point.

This module is intentionally thin: it wires together configuration,
the HTTP client, and all tool/resource registrations.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from stream_mcp.client import StreamClient
from stream_mcp.config import settings
from stream_mcp.tools import register_all_tools

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Create a shared :class:`StreamClient` for the server lifetime."""
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


def main() -> None:
    """CLI entry-point (``stream-mcp`` command)."""
    mcp.run()


if __name__ == "__main__":
    main()
