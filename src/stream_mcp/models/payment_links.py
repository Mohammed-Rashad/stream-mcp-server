"""Pydantic models for the Payment Links resource."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PaymentLinkItem(BaseModel):
    """A single line-item inside a payment link."""

    product_id: str = Field(..., description="ID of the product to include.")
    quantity: int = Field(ge=1, description="Number of units (≥ 1).")
    coupons: list[str] = Field(default_factory=list, description="Coupon IDs to apply to this item.")


class CreatePaymentLinkRequest(BaseModel):
    """Request body for creating a new payment link."""

    name: str = Field(..., description="Display name for the payment link.")
    items: list[PaymentLinkItem] = Field(..., min_length=1, description="Line-items (product + quantity + coupons). Cannot mix one-time and recurring products.")
    description: str | None = Field(default=None, description="Optional description shown on the checkout page.")
    currency: str = Field(default="SAR", description="ISO-4217 currency code.")
    coupons: list[str] | None = Field(default=None, description="Coupon IDs to apply.")
    max_number_of_payments: int | None = Field(default=None, description="Maximum number of payments allowed.")
    valid_until: str | None = Field(default=None, description="ISO-8601 expiry timestamp. Null = never expires.")
    success_redirect_url: str | None = Field(default=None, description="URL to redirect to after successful payment.")
    failure_redirect_url: str | None = Field(default=None, description="URL to redirect to after failed payment.")
    organization_consumer_id: str | None = Field(default=None, description="Pre-assign a customer to this link.")


class UpdatePaymentLinkStatusRequest(BaseModel):
    """Request body for updating a payment link status."""

    status: str = Field(..., description="New status: INACTIVE, ACTIVE, or COMPLETED.")
    deactivate_message: str | None = Field(default=None, description="Message shown when link is deactivated.")


class PaymentLinkResponse(BaseModel):
    """Subset of fields returned by the Stream API for a payment link."""

    id: str
    url: str | None = None
    status: str | None = None
    name: str | None = None
    description: str | None = None
    created_at: str | None = None

    model_config = {"extra": "allow"}


class PaymentLinkListResponse(BaseModel):
    """Paginated list of payment links."""

    data: list[dict] = Field(default_factory=list)
    total: int | None = None
    page: int | None = None
    limit: int | None = None

    model_config = {"extra": "allow"}
