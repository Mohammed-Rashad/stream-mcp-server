"""MCP tools for the Coupons resource."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from fastmcp.server.context import Context

from stream_mcp.client import StreamAPIError
from stream_mcp.helpers import get_client
from stream_mcp.models.coupons import (
    CreateCouponRequest,
    UpdateCouponRequest,
)

_BASE = "/api/v2/coupons"


def _err(exc: StreamAPIError) -> dict[str, Any]:
    return {"error": True, "code": exc.status_code, "message": str(exc), "details": exc.body}


def register(mcp: FastMCP) -> None:
    """Register all coupon tools on *mcp*."""

    @mcp.tool
    async def create_coupon(
        name: str,
        discount_value: float,
        is_percentage: bool = False,
        currency: str | None = None,
        is_active: bool = True,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Create a new discount coupon on Stream.

        Set *is_percentage* to True for percentage discount, False for fixed amount.
        For fixed coupons, *currency* is required (e.g. SAR, USD).
        """
        body = CreateCouponRequest(
            name=name,
            discount_value=discount_value,
            is_percentage=is_percentage,
            currency=currency,
            is_active=is_active,
        )
        client = await get_client(ctx)
        try:
            return await client.post(_BASE, body.model_dump(exclude_none=True))
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def list_coupons(
        page: int = 1,
        limit: int = 20,
        active: bool | None = None,
        is_percentage: bool | None = None,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """List all coupons with optional filters.

        *active* filters by active/inactive status.
        *is_percentage* filters by discount type.
        """
        params: dict[str, Any] = {"page": page, "limit": limit}
        if active is not None:
            params["active"] = active
        if is_percentage is not None:
            params["is_percentage"] = is_percentage
        client = await get_client(ctx)
        try:
            return await client.get(_BASE, params=params)
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def get_coupon(
        coupon_id: str,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Get a single coupon by ID."""
        client = await get_client(ctx)
        try:
            return await client.get(f"{_BASE}/{coupon_id}")
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def deactivate_coupon(
        coupon_id: str,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Deactivate a coupon so it can no longer be redeemed."""
        body = UpdateCouponRequest(is_active=False)
        client = await get_client(ctx)
        try:
            return await client.put(
                f"{_BASE}/{coupon_id}",
                body.model_dump(exclude_none=True),
            )
        except StreamAPIError as exc:
            return _err(exc)
