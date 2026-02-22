"""MCP tools for the Products resource."""

from __future__ import annotations

from typing import Any, Literal

from fastmcp import FastMCP
from fastmcp.server.context import Context

from stream_mcp.client import StreamAPIError
from stream_mcp.models.products import (
    CreateProductRequest,
    ProductPriceInlineCreate,
    UpdateProductRequest,
)

_BASE = "/api/v2/products"


def _err(exc: StreamAPIError) -> dict[str, Any]:
    return {"error": True, "code": exc.status_code, "message": str(exc), "details": exc.body}


def register(mcp: FastMCP) -> None:
    """Register all product tools on *mcp*."""

    @mcp.tool
    async def create_product(
        name: str,
        type: Literal["ONE_OFF", "RECURRING", "METERED"] = "ONE_OFF",
        price: float = 1.0,
        currency: str = "SAR",
        description: str | None = None,
        is_price_inclusive_of_vat: bool = True,
        is_price_exempt_from_vat: bool = False,
        recurring_interval: str | None = None,
        recurring_interval_count: int = 1,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Create a new product or service in Stream.

        *type* is ``ONE_OFF``, ``RECURRING``, or ``METERED``.
        For recurring products, specify *recurring_interval* (WEEK, MONTH, SEMESTER, YEAR).
        """
        prices = [ProductPriceInlineCreate(
            currency=currency,
            amount=price,
            is_price_inclusive_of_vat=is_price_inclusive_of_vat,
            is_price_exempt_from_vat=is_price_exempt_from_vat,
        )]
        body = CreateProductRequest(
            name=name,
            type=type,
            description=description,
            prices=prices,
            recurring_interval=recurring_interval,
            recurring_interval_count=recurring_interval_count,
        )
        client = ctx.lifespan_context["client"]
        try:
            return await client.post(_BASE, body.model_dump(exclude_none=True))
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def list_products(
        page: int = 1,
        limit: int = 20,
        type: str | None = None,
        active: bool | None = None,
        currency: str | None = None,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """List products with optional filters.

        *type* can be ``ONE_OFF``, ``RECURRING``, or ``METERED``.
        *active* filters by active/inactive status.
        """
        params: dict[str, Any] = {"page": page, "limit": limit}
        if type:
            params["type"] = type
        if active is not None:
            params["active"] = active
        if currency:
            params["currency"] = currency
        client = ctx.lifespan_context["client"]
        try:
            return await client.get(_BASE, params=params)
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def get_product(
        product_id: str,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Get a single product by ID."""
        client = ctx.lifespan_context["client"]
        try:
            return await client.get(f"{_BASE}/{product_id}")
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def update_product(
        product_id: str,
        name: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Update an existing product's name, description, or active status.

        Only the fields you provide will be changed.
        """
        body = UpdateProductRequest(
            name=name, description=description, is_active=is_active,
        )
        client = ctx.lifespan_context["client"]
        try:
            return await client.put(
                f"{_BASE}/{product_id}",
                body.model_dump(exclude_none=True),
            )
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def archive_product(
        product_id: str,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Archive a product so it can no longer be sold.

        This is a soft-delete; the product record is retained for history.
        """
        client = ctx.lifespan_context["client"]
        try:
            return await client.delete(f"{_BASE}/{product_id}")
        except StreamAPIError as exc:
            return _err(exc)
