from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PaymentGatewayProvider(str, enum.Enum):
    PHONEPE = "phonepe"
    RAZORPAY = "razorpay"
    PAYTM = "paytm"
    STRIPE = "stripe"
    PAYPAL = "paypal"
    CASHFREE = "cashfree"
    CUSTOM = "custom"


class PaymentGatewayEnvironment(str, enum.Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class PaymentGatewayStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISABLED = "disabled"


class PaymentGateway(Base):
    """Restaurant-scoped payment gateway credentials and configuration."""

    __tablename__ = "payment_gateways"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "provider", name="uq_payment_gateways_restaurant_provider"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        SQLEnum(
            PaymentGatewayProvider,
            native_enum=False,
            length=30,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        index=True,
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    environment: Mapped[str] = mapped_column(
        SQLEnum(
            PaymentGatewayEnvironment,
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=PaymentGatewayEnvironment.SANDBOX,
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(
            PaymentGatewayStatus,
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=PaymentGatewayStatus.INACTIVE,
        nullable=False,
        index=True,
    )

    api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    client_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    secret_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    merchant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    salt_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    salt_index: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    upi_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    callback_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    extra_config: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<PaymentGateway(id={self.id}, restaurant_id={self.restaurant_id}, "
            f"provider={self.provider}, environment={self.environment})>"
        )
