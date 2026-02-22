"""Pydantic models for the Payments resource."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MarkPaymentPaidRequest(BaseModel):
    """Request body for marking a payment as paid."""

    payment_method: str = Field(
        ...,
        description="Manual payment method used: CASH, BANK_TRANSFER, CARD, or QURRAH.",
    )
    note: str | None = Field(default=None, description="Optional note or reference number for the payment.")


class RefundPaymentRequest(BaseModel):
    """Request body for issuing a refund on a payment."""

    refund_reason: str = Field(
        ...,
        description="Reason for the refund: REQUESTED_BY_CUSTOMER, DUPLICATE, FRAUDULENT, or OTHER.",
    )
    refund_note: str | None = Field(default=None, description="Additional note about the refund.")
    allow_refund_multiple_related_payments: bool = Field(
        default=False, description="Whether to also refund related payments.",
    )


class PaymentResponse(BaseModel):
    """Subset of fields returned by the Stream API for a payment."""

    id: str
    amount: float | None = None
    currency: str | None = None
    status: str | None = None
    customer_id: str | None = None
    payment_method: str | None = None
    created_at: str | None = None

    model_config = {"extra": "allow"}


class PaymentListResponse(BaseModel):
    """Paginated list of payments."""

    data: list[dict] = Field(default_factory=list)
    total: int | None = None
    page: int | None = None
    limit: int | None = None

    model_config = {"extra": "allow"}
