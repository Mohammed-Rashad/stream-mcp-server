"""Pydantic models for the Coupons resource."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateCouponRequest(BaseModel):
    """Request body for creating a new coupon."""

    name: str = Field(..., min_length=1, max_length=80, description="Coupon display name.")
    discount_value: float = Field(..., ge=0, description="Discount value (amount or percentage).")
    currency: str | None = Field(
        default=None,
        description="ISO-4217 currency code. Required when is_percentage is false. Must be null when is_percentage is true.",
    )
    is_percentage: bool = Field(default=False, description="True for percentage discount, false for fixed amount.")
    is_active: bool = Field(default=True, description="Whether the coupon is active.")


class UpdateCouponRequest(BaseModel):
    """Request body for updating a coupon."""

    name: str | None = Field(default=None, min_length=1, max_length=80, description="Updated coupon name.")
    discount_value: float | None = Field(default=None, ge=0, description="Updated discount value.")
    currency: str | None = Field(default=None, description="Updated currency code.")
    is_percentage: bool | None = Field(default=None, description="Updated discount type.")
    is_active: bool | None = Field(default=None, description="Updated active status.")


class CouponResponse(BaseModel):
    """Subset of fields returned by the Stream API for a coupon."""

    id: str
    name: str | None = None
    type: str | None = None
    value: float | None = None
    status: str | None = None
    created_at: str | None = None

    model_config = {"extra": "allow"}


class CouponListResponse(BaseModel):
    """Paginated list of coupons."""

    data: list[dict] = Field(default_factory=list)
    total: int | None = None
    page: int | None = None
    limit: int | None = None

    model_config = {"extra": "allow"}
