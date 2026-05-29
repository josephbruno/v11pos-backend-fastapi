from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.payment_gateway.model import (
    PaymentGateway,
    PaymentGatewayEnvironment,
    PaymentGatewayProvider,
    PaymentGatewayStatus,
)


class PaymentGatewayBase(BaseModel):
    provider: PaymentGatewayProvider
    display_name: Optional[str] = Field(None, max_length=100)
    environment: PaymentGatewayEnvironment = PaymentGatewayEnvironment.SANDBOX
    status: PaymentGatewayStatus = PaymentGatewayStatus.INACTIVE
    api_key: Optional[str] = Field(None, max_length=500)
    client_id: Optional[str] = Field(None, max_length=255)
    secret_key: Optional[str] = Field(None, max_length=500)
    merchant_id: Optional[str] = Field(None, max_length=255)
    salt_key: Optional[str] = Field(None, max_length=500)
    salt_index: Optional[str] = Field(None, max_length=50)
    webhook_secret: Optional[str] = Field(None, max_length=500)
    upi_id: Optional[str] = Field(None, max_length=100)
    base_url: Optional[str] = Field(None, max_length=500)
    webhook_url: Optional[str] = Field(None, max_length=500)
    callback_url: Optional[str] = Field(None, max_length=500)
    extra_config: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    is_active: bool = True
    is_default: bool = False


class PaymentGatewayCreate(PaymentGatewayBase):
    restaurant_id: str


class PaymentGatewayUpdate(BaseModel):
    provider: Optional[PaymentGatewayProvider] = None
    display_name: Optional[str] = Field(None, max_length=100)
    environment: Optional[PaymentGatewayEnvironment] = None
    status: Optional[PaymentGatewayStatus] = None
    api_key: Optional[str] = Field(None, max_length=500)
    client_id: Optional[str] = Field(None, max_length=255)
    secret_key: Optional[str] = Field(None, max_length=500)
    merchant_id: Optional[str] = Field(None, max_length=255)
    salt_key: Optional[str] = Field(None, max_length=500)
    salt_index: Optional[str] = Field(None, max_length=50)
    webhook_secret: Optional[str] = Field(None, max_length=500)
    upi_id: Optional[str] = Field(None, max_length=100)
    base_url: Optional[str] = Field(None, max_length=500)
    webhook_url: Optional[str] = Field(None, max_length=500)
    callback_url: Optional[str] = Field(None, max_length=500)
    extra_config: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class PaymentGatewayResponse(BaseModel):
    id: str
    restaurant_id: str
    provider: PaymentGatewayProvider
    display_name: Optional[str] = None
    environment: PaymentGatewayEnvironment
    status: PaymentGatewayStatus
    merchant_id: Optional[str] = None
    salt_index: Optional[str] = None
    upi_id: Optional[str] = None
    base_url: Optional[str] = None
    webhook_url: Optional[str] = None
    callback_url: Optional[str] = None
    extra_config: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    is_active: bool
    is_default: bool
    has_api_key: bool
    has_client_id: bool
    has_secret_key: bool
    has_salt_key: bool
    has_webhook_secret: bool
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, gateway: PaymentGateway) -> "PaymentGatewayResponse":
        return cls(
            id=gateway.id,
            restaurant_id=gateway.restaurant_id,
            provider=gateway.provider,
            display_name=gateway.display_name,
            environment=gateway.environment,
            status=gateway.status,
            merchant_id=gateway.merchant_id,
            salt_index=gateway.salt_index,
            upi_id=gateway.upi_id,
            base_url=gateway.base_url,
            webhook_url=gateway.webhook_url,
            callback_url=gateway.callback_url,
            extra_config=gateway.extra_config,
            notes=gateway.notes,
            is_active=gateway.is_active,
            is_default=gateway.is_default,
            has_api_key=bool(gateway.api_key),
            has_client_id=bool(gateway.client_id),
            has_secret_key=bool(gateway.secret_key),
            has_salt_key=bool(gateway.salt_key),
            has_webhook_secret=bool(gateway.webhook_secret),
            created_by=gateway.created_by,
            updated_by=gateway.updated_by,
            created_at=gateway.created_at,
            updated_at=gateway.updated_at,
        )
