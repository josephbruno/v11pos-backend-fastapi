"""
Order payment schemas.

Required fields to **record** a payment row (manual or split):
- ``order_id`` — target order
- ``restaurant_id`` — owning restaurant (for scoping and reporting)
- ``amount`` — amount in minor units (paise/cents), ≥ 0

When an order is created, the API automatically inserts one row with ``amount`` = order
``total_amount``, ``payment_status`` = ``pending``, and no ``payment_method`` until capture.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.order.model import PaymentMethod, PaymentStatus


class OrderPaymentCreate(BaseModel):
    """Create a payment leg against an order (e.g. split tender)."""

    order_id: str = Field(..., description="Order this payment applies to")
    restaurant_id: str = Field(..., description="Restaurant scope")
    amount: int = Field(..., ge=0, description="Amount in minor units")
    currency: str = Field(default="INR", min_length=3, max_length=3)
    payment_method: Optional[PaymentMethod] = None
    payment_status: Optional[PaymentStatus] = Field(
        default=None,
        description="Defaults to pending when omitted",
    )
    gateway: Optional[str] = Field(None, max_length=50)
    gateway_transaction_id: Optional[str] = Field(None, max_length=100)
    payment_reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    payment_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Gateway payload, idempotency keys, etc.",
    )


class OrderPaymentUpdate(BaseModel):
    """Update capture / reconciliation fields on a payment row."""

    payment_status: Optional[PaymentStatus] = None
    payment_method: Optional[PaymentMethod] = None
    gateway: Optional[str] = Field(None, max_length=50)
    gateway_transaction_id: Optional[str] = Field(None, max_length=100)
    payment_reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    payment_metadata: Optional[Dict[str, Any]] = None


class OrderPaymentResponse(BaseModel):
    id: str
    restaurant_id: str
    order_id: str
    amount: int
    currency: str
    payment_status: PaymentStatus
    payment_method: Optional[PaymentMethod] = None
    gateway: Optional[str] = None
    gateway_transaction_id: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    extra_metadata: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
