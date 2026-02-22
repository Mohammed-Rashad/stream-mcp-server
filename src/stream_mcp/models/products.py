"""Pydantic models for the Products resource."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProductPriceInlineCreate(BaseModel):
    """Inline price definition for product creation."""

    currency: str = Field(default="SAR", description="ISO-4217 currency code (SAR, USD, EUR, etc.).")
    amount: float = Field(..., ge=1, description="Price amount (≥ 1).")
    is_price_inclusive_of_vat: bool = Field(default=True, description="Whether price includes VAT.")
    is_price_exempt_from_vat: bool = Field(default=False, description="Whether price is VAT-exempt.")


class CreateProductRequest(BaseModel):
    """Request body for creating a new product."""

    name: str = Field(..., min_length=1, max_length=160, description="Product display name.")
    type: Literal["ONE_OFF", "RECURRING", "METERED"] = Field(
        ...,
        description="Product billing type: ONE_OFF, RECURRING, or METERED.",
    )
    description: str | None = Field(default=None, max_length=500, description="Product description.")
    prices: list[ProductPriceInlineCreate] | None = Field(default=None, description="List of prices for different currencies.")
    is_one_time: bool = Field(default=False, description="Whether the product is one-time use.")
    recurring_interval: str | None = Field(
        default=None,
        description="Billing interval for recurring products: WEEK, MONTH, SEMESTER, YEAR.",
    )
    recurring_interval_count: int = Field(default=1, ge=1, description="Number of intervals between billings.")


class UpdateProductRequest(BaseModel):
    """Request body for updating an existing product."""

    name: str | None = Field(default=None, min_length=1, max_length=160, description="Updated product name.")
    description: str | None = Field(default=None, max_length=500, description="Updated description.")
    prices: list[ProductPriceInlineCreate] | None = Field(default=None, description="Updated prices.")
    is_active: bool | None = Field(default=None, description="Whether the product is active.")
    type: Literal["ONE_OFF", "RECURRING", "METERED"] | None = Field(default=None, description="Updated product type.")
    recurring_interval: str | None = Field(default=None, description="Updated billing interval.")
    recurring_interval_count: int | None = Field(default=None, ge=1, description="Updated interval count.")


class ProductResponse(BaseModel):
    """Subset of fields returned by the Stream API for a product."""

    id: str
    name: str | None = None
    description: str | None = None
    price: float | None = None
    currency: str | None = None
    type: str | None = None
    created_at: str | None = None

    model_config = {"extra": "allow"}


class ProductListResponse(BaseModel):
    """Paginated list of products."""

    data: list[dict] = Field(default_factory=list)
    total: int | None = None
    page: int | None = None
    limit: int | None = None

    model_config = {"extra": "allow"}
