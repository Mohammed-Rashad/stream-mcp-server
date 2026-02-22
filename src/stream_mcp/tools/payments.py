"""MCP tools for the Payments resource."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from fastmcp.server.context import Context

from stream_mcp.client import StreamAPIError
from stream_mcp.models.payments import MarkPaymentPaidRequest, RefundPaymentRequest

_BASE = "/api/v2/payments"


def _err(exc: StreamAPIError) -> dict[str, Any]:
    return {"error": True, "code": exc.status_code, "message": str(exc), "details": exc.body}


def register(mcp: FastMCP) -> None:
    """Register all payment tools on *mcp*."""

    @mcp.tool
    async def list_payments(
        page: int = 1,
        limit: int = 20,
        statuses: list[str] | None = None,
        invoice_id: str | None = None,
        search_term: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """List payments with optional filters.

        Filter by *statuses* (PENDING, PROCESSING, SUCCEEDED, FAILED, CANCELED,
        UNDER_REVIEW, EXPIRED, SETTLED, REFUNDED), *invoice_id*, *search_term*,
        or a date range (*from_date* / *to_date* in ISO-8601).
        """
        params: dict[str, Any] = {"page": page, "limit": limit}
        if statuses:
            params["statuses"] = statuses
        if invoice_id:
            params["invoice_id"] = invoice_id
        if search_term:
            params["search_term"] = search_term
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
    async def get_payment(
        payment_id: str,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Get details of a single payment by ID.

        Returns amount, status, payment method, customer info, and more.
        """
        client = ctx.lifespan_context["client"]
        try:
            return await client.get(f"{_BASE}/{payment_id}")
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def mark_payment_as_paid(
        payment_id: str,
        payment_method: str = "CASH",
        note: str | None = None,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Manually mark a payment as paid.

        Record a payment received through manual methods.
        *payment_method* must be one of: CASH, BANK_TRANSFER, CARD, or QURRAH.
        """
        body = MarkPaymentPaidRequest(
            payment_method=payment_method,
            note=note,
        )
        client = ctx.lifespan_context["client"]
        try:
            return await client.post(
                f"{_BASE}/{payment_id}/mark-paid",
                body.model_dump(exclude_none=True),
            )
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def refund_payment(
        payment_id: str,
        refund_reason: str = "REQUESTED_BY_CUSTOMER",
        refund_note: str | None = None,
        allow_refund_multiple_related_payments: bool = False,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Issue a refund on a completed payment.

        *refund_reason* must be one of: REQUESTED_BY_CUSTOMER, DUPLICATE, FRAUDULENT, OTHER.
        """
        body = RefundPaymentRequest(
            refund_reason=refund_reason,
            refund_note=refund_note,
            allow_refund_multiple_related_payments=allow_refund_multiple_related_payments,
        )
        client = ctx.lifespan_context["client"]
        try:
            return await client.post(
                f"{_BASE}/{payment_id}/refund",
                body.model_dump(exclude_none=True),
            )
        except StreamAPIError as exc:
            return _err(exc)
