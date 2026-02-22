"""Pydantic models for the Customers resource."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateCustomerRequest(BaseModel):
    """Request body for creating a new customer."""

    name: str = Field(..., description="Full name of the customer.")
    phone_number: str | None = Field(default=None, description="Customer phone number (E.164 recommended).")
    email: str | None = Field(default=None, description="Customer email address.")
    external_id: str | None = Field(default=None, description="External system ID for the customer.")
    iban: str | None = Field(default=None, max_length=34, description="Customer IBAN (max 34 chars).")
    alias: str | None = Field(default=None, description="Customer alias / nickname.")
    comment: str | None = Field(default=None, description="Internal comment about the customer.")
    preferred_language: str | None = Field(default=None, description="Preferred language (e.g. EN, AR).")
    communication_methods: list[str] | None = Field(default=None, description="Communication methods: WHATSAPP, EMAIL, SMS.")


class UpdateCustomerRequest(BaseModel):
    """Request body for updating an existing customer."""

    name: str | None = Field(default=None, description="Updated name.")
    phone_number: str | None = Field(default=None, description="Updated phone number.")
    email: str | None = Field(default=None, description="Updated email address.")
    external_id: str | None = Field(default=None, description="Updated external system ID.")
    iban: str | None = Field(default=None, max_length=34, description="Updated IBAN.")
    alias: str | None = Field(default=None, description="Updated alias / nickname.")
    comment: str | None = Field(default=None, description="Updated internal comment.")
    preferred_language: str | None = Field(default=None, description="Updated preferred language.")
    communication_methods: list[str] | None = Field(default=None, description="Updated communication methods.")


class CustomerResponse(BaseModel):
    """Subset of fields returned by the Stream API for a customer."""

    id: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    created_at: str | None = None

    model_config = {"extra": "allow"}


class CustomerListResponse(BaseModel):
    """Paginated list of customers."""

    data: list[dict] = Field(default_factory=list)
    total: int | None = None
    page: int | None = None
    limit: int | None = None

    model_config = {"extra": "allow"}
