"""MCP tools for the Customers resource."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from fastmcp.server.context import Context

from stream_mcp.client import StreamAPIError
from stream_mcp.models.customers import (
    CreateCustomerRequest,
    UpdateCustomerRequest,
)

_BASE = "/api/v2/consumers"


def _err(exc: StreamAPIError) -> dict[str, Any]:
    return {"error": True, "code": exc.status_code, "message": str(exc), "details": exc.body}


def register(mcp: FastMCP) -> None:
    """Register all customer tools on *mcp*."""

    @mcp.tool
    async def create_customer(
        name: str,
        phone_number: str | None = None,
        email: str | None = None,
        external_id: str | None = None,
        iban: str | None = None,
        alias: str | None = None,
        comment: str | None = None,
        preferred_language: str | None = None,
        communication_methods: list[str] | None = None,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Create a new customer in Stream.

        Provide at least a *name*. Optionally include *phone_number*, *email*,
        *external_id*, *iban*, *alias*, *comment*, *preferred_language* (EN/AR),
        and *communication_methods* (WHATSAPP, EMAIL, SMS).
        """
        body = CreateCustomerRequest(
            name=name, phone_number=phone_number, email=email,
            external_id=external_id, iban=iban, alias=alias,
            comment=comment, preferred_language=preferred_language,
            communication_methods=communication_methods,
        )
        client = ctx.lifespan_context["client"]
        try:
            return await client.post(_BASE, body.model_dump(exclude_none=True))
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def list_customers(
        page: int = 1,
        limit: int = 20,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """List / search customers with pagination.

        Returns a paginated list of customers.
        """
        params: dict[str, Any] = {"page": page, "limit": limit}
        client = ctx.lifespan_context["client"]
        try:
            return await client.get(_BASE, params=params)
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def get_customer(
        customer_id: str,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Get a single customer record by ID."""
        client = ctx.lifespan_context["client"]
        try:
            return await client.get(f"{_BASE}/{customer_id}")
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def update_customer(
        customer_id: str,
        name: str | None = None,
        phone_number: str | None = None,
        email: str | None = None,
        external_id: str | None = None,
        iban: str | None = None,
        alias: str | None = None,
        comment: str | None = None,
        preferred_language: str | None = None,
        communication_methods: list[str] | None = None,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Update fields on an existing customer.

        Only the fields you provide will be changed; others remain untouched.
        """
        body = UpdateCustomerRequest(
            name=name, phone_number=phone_number, email=email,
            external_id=external_id, iban=iban, alias=alias,
            comment=comment, preferred_language=preferred_language,
            communication_methods=communication_methods,
        )
        client = ctx.lifespan_context["client"]
        try:
            return await client.put(
                f"{_BASE}/{customer_id}",
                body.model_dump(exclude_none=True),
            )
        except StreamAPIError as exc:
            return _err(exc)

    @mcp.tool
    async def delete_customer(
        customer_id: str,
        ctx: Context = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        """Soft-delete a customer by ID.

        The customer record is archived but not permanently removed.
        """
        client = ctx.lifespan_context["client"]
        try:
            return await client.delete(f"{_BASE}/{customer_id}")
        except StreamAPIError as exc:
            return _err(exc)
