"""Pydantic models for the Invoices resource."""

from __future__ import annotations

from pydantic import BaseModel, Field


class InvoiceItemCreateDto(BaseModel):
    """A single line-item on an invoice."""

    product_id: str = Field(..., description="ID of the product.")
    quantity: int = Field(..., gt=0, description="Quantity (> 0).")
    coupons: list[str] | None = Field(default=None, description="Coupon IDs to apply to this item.")


class InvoicePaymentMethodDto(BaseModel):
    """Payment methods accepted for an invoice."""

    mada: bool = Field(default=True, description="Accept Mada payments.")
    visa: bool = Field(default=True, description="Accept Visa payments.")
    mastercard: bool = Field(default=True, description="Accept Mastercard payments.")
    amex: bool = Field(default=False, description="Accept Amex payments.")
    bank_transfer: bool = Field(default=False, description="Accept bank transfer.")
    installment: bool = Field(default=False, description="Accept installment payments.")
    qurrah: bool = Field(default=False, description="Accept Qurrah payments.")


class CreateInvoiceRequest(BaseModel):
    """Request body for creating a new invoice."""

    organization_consumer_id: str = Field(..., description="Customer (consumer) ID to invoice.")
    items: list[InvoiceItemCreateDto] = Field(..., min_length=1, description="Line-items on the invoice.")
    payment_methods: InvoicePaymentMethodDto = Field(
        default_factory=InvoicePaymentMethodDto,
        description="Payment methods accepted for this invoice.",
    )
    scheduled_on: str = Field(..., description="ISO-8601 date-time when the invoice should be sent/due.")
    notify_consumer: bool = Field(default=True, description="Send the invoice to the customer upon creation.")
    description: str | None = Field(default=None, max_length=500, description="Invoice memo / description.")
    coupons: list[str] | None = Field(default=None, description="Coupon IDs to apply to the whole invoice.")
    currency: str = Field(default="SAR", description="ISO-4217 currency code.")


class InvoiceResponse(BaseModel):
    """Subset of fields returned by the Stream API for an invoice."""

    id: str
    customer_id: str | None = None
    status: str | None = None
    total: float | None = None
    currency: str | None = None
    created_at: str | None = None

    model_config = {"extra": "allow"}


class InvoiceListResponse(BaseModel):
    """Paginated list of invoices."""

    data: list[dict] = Field(default_factory=list)
    total: int | None = None
    page: int | None = None
    limit: int | None = None

    model_config = {"extra": "allow"}
