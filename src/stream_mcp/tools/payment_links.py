"""MCP tools for the Payment Links resource."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from fastmcp.server.context import Context

from stream_mcp.client import StreamAPIError
from stream_mcp.helpers import get_client
from stream_mcp.models.payment_links import (
    CreatePaymentLinkRequest,
    UpdatePaymentLinkStatusRequest,
)

_BASE = "/api/v2/payment_links"


def _err(exc: StreamAPIError) -> dict[str, Any]:
    return {"error": True, "code": exc.status_code, "message": str(exc), "details": exc.body}


def register(mcp: FastMCP) -> None:
    """Register all payment-link tools on *mcp*."""

    @mcp.tool
    async def create_payment_link(
        name: str,
        items: list[dict],
        description: str | None = None,
        currency: str = "SAR",
        valid_until: str | None = None,
        max_number_of_payments: int | None = None,
        organization_consumer_id: str | None = None,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Create a new payment / checkout link on Stream.

        *items* is a list of objects, each containing:
          - product_id (str, required)
          - quantity   (int ≥ 1, optional, default 1)
          - coupons    (list[str], optional)

        You **cannot** mix one-time and recurring products in the same link.
        """
        body = CreatePaymentLinkRequest(
            name=name,
            items=items,  # type: ignore[arg-type]
            description=description,
            currency=currency,
            valid_until=valid_until,
            max_number_of_payments=max_number_of_payments,
            organization_consumer_id=organization_consumer_id,
        )
        client = await get_client(ctx)
        try:
            return await client.post(_BASE, body.model_dump(exclude_none=True))
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def list_payment_links(
        page: int = 1,
        limit: int = 20,
        statuses: list[str] | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """List all payment links with optional filters.

        *statuses* can include: INACTIVE, ACTIVE, COMPLETED.
        """
        params: dict[str, Any] = {"page": page, "limit": limit}
        if statuses:
            params["statuses"] = statuses
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        client = await get_client(ctx)
        try:
            return await client.get(_BASE, params=params)
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def get_payment_link(
        payment_link_id: str,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Retrieve a single payment link by its ID."""
        client = await get_client(ctx)
        try:
            return await client.get(f"{_BASE}/{payment_link_id}")
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def deactivate_payment_link(
        payment_link_id: str,
        deactivate_message: str | None = None,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Deactivate (archive) a payment link so it can no longer be used."""
        body = UpdatePaymentLinkStatusRequest(
            status="INACTIVE",
            deactivate_message=deactivate_message,
        )
        client = await get_client(ctx)
        try:
            return await client.patch(
                f"{_BASE}/{payment_link_id}/status",
                body.model_dump(exclude_none=True),
            )
        except StreamAPIError as exc:
            return _err(exc)
