"""Tool & resource registration — one import line per resource domain.

Adding a new resource = add one ``from … import register`` line and one call.
"""

from __future__ import annotations

from fastmcp import FastMCP


def register_all_tools(mcp: FastMCP) -> None:
    """Import every tool / resource module and call its ``register(mcp)``."""
    from stream_mcp.tools import (
        coupons,
        customers,
        docs,
        invoices,
        payment_links,
        payments,
        products,
    )

    payment_links.register(mcp)
    customers.register(mcp)
    products.register(mcp)
    payments.register(mcp)
    coupons.register(mcp)
    invoices.register(mcp)
    docs.register(mcp)
