"""MCP tools for the Invoices resource."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastmcp import FastMCP
from fastmcp.server.context import Context

from stream_mcp.client import StreamAPIError
from stream_mcp.models.invoices import (
    CreateInvoiceRequest,
    InvoiceItemCreateDto,
    InvoicePaymentMethodDto,
)

_BASE = "/api/v2/invoices"


def _err(exc: StreamAPIError) -> dict[str, Any]:
    return {"error": True, "code": exc.status_code, "message": str(exc), "details": exc.body}


def register(mcp: FastMCP) -> None:
    """Register all invoice tools on *mcp*."""

    @mcp.tool
    async def create_invoice(
        customer_id: str,
        items: list[dict],
        scheduled_on: str | None = None,
        description: str | None = None,
        currency: str = "SAR",
        notify_consumer: bool = True,
        coupons: list[str] | None = None,
        accept_mada: bool = True,
        accept_visa: bool = True,
        accept_mastercard: bool = True,
        accept_amex: bool = False,
        accept_bank_transfer: bool = False,
        accept_installment: bool = False,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Create a ZATCA-compliant invoice in Stream.

        *items* is a list of line-item dicts, each with:
          - product_id  (str, required)
          - quantity    (int > 0, required)

        *scheduled_on* is the ISO-8601 date-time for when the invoice is due/sent.
        Set *notify_consumer* to True to send the invoice to the customer.
        """
        parsed_items = [InvoiceItemCreateDto(**item) for item in items]
        if scheduled_on is None:
            scheduled_on = datetime.now(timezone.utc).isoformat()
        payment_methods = InvoicePaymentMethodDto(
            mada=accept_mada,
            visa=accept_visa,
            mastercard=accept_mastercard,
            amex=accept_amex,
            bank_transfer=accept_bank_transfer,
            installment=accept_installment,
        )
        body = CreateInvoiceRequest(
            organization_consumer_id=customer_id,
            items=parsed_items,
            payment_methods=payment_methods,
            scheduled_on=scheduled_on,
            notify_consumer=notify_consumer,
            description=description,
            coupons=coupons,
            currency=currency,
        )
        client = ctx.lifespan_context["client"]
        try:
            return await client.post(_BASE, body.model_dump(exclude_none=True))
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def list_invoices(
        page: int = 1,
        limit: int = 20,
        organization_consumer_id: str | None = None,
        statuses: list[str] | None = None,
        payment_statuses: list[str] | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """List invoices with optional filters.

        Filter by *organization_consumer_id*, *statuses* (DRAFT, CREATED, SENT, ACCEPTED,
        REJECTED, COMPLETED, CANCELED, EXPIRED), *payment_statuses* (PENDING, PROCESSING,
        SUCCEEDED, FAILED, etc.), or a date range.
        """
        params: dict[str, Any] = {"page": page, "limit": limit}
        if organization_consumer_id:
            params["organization_consumer_id"] = organization_consumer_id
        if statuses:
            params["statuses"] = statuses
        if payment_statuses:
            params["payment_statuses"] = payment_statuses
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        client = ctx.lifespan_context["client"]
        try:
            return await client.get(_BASE, params=params)
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def get_invoice(
        invoice_id: str,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Get a single invoice by ID."""
        client = ctx.lifespan_context["client"]
        try:
            return await client.get(f"{_BASE}/{invoice_id}")
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def send_invoice(
        invoice_id: str,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """(Re)send an invoice to the customer via email / SMS."""
        client = ctx.lifespan_context["client"]
        try:
            return await client.post(f"{_BASE}/{invoice_id}/send", body={})
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def void_invoice(
        invoice_id: str,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Void (cancel) an unpaid invoice.

        Once voided, the invoice can no longer be paid.
        """
        client = ctx.lifespan_context["client"]
        try:
            return await client.post(f"{_BASE}/{invoice_id}/void", body={})
        except StreamAPIError as exc:
            return _err(exc)
