"""
QR Ordering Pydantic schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, List
from datetime import datetime
from app.enums import QRSessionStatus


# QR Table Schemas
class QRTableBase(BaseModel):
    table_number: str = Field(..., min_length=1, max_length=20)
    table_name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(default='Main Floor', max_length=100)
    capacity: int = Field(default=4, ge=1, le=50)
    is_active: bool = True


class QRTableCreate(QRTableBase):
    pass


class QRTableUpdate(BaseModel):
    table_name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=100)
    capacity: Optional[int] = Field(None, ge=1, le=50)
    is_active: Optional[bool] = None


class QRTableResponse(QRTableBase):
    id: str
    qr_token: str
    qr_code_url: str
    qr_code_image: Optional[str] = None
    is_occupied: bool
    current_session_id: Optional[str] = None
    created_at: datetime
    last_used: Optional[datetime] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True


# QR Session Schemas
class QRSessionBase(BaseModel):
    customer_name: str = "Guest"
    customer_phone: Optional[str] = None
    guest_count: int = Field(default=1, ge=1, le=50)


class QRSessionCreate(QRSessionBase):
    table_id: str
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class QRSessionUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    guest_count: Optional[int] = Field(None, ge=1, le=50)
    status: Optional[QRSessionStatus] = None


class QRSessionResponse(QRSessionBase):
    id: str
    table_id: str
    customer_id: Optional[str] = None
    device_fingerprint: Optional[str] = None
    status: QRSessionStatus
    cart_items: int
    cart_total: int
    orders_placed: int
    total_spent: int
    start_time: datetime
    end_time: Optional[datetime] = None
    last_activity: datetime
    created_at: datetime
    
    @property
    def cart_total_display(self) -> float:
        return self.cart_total / 100
    
    @property
    def total_spent_display(self) -> float:
        return self.total_spent / 100
    
    class Config:
        from_attributes = True


# QR Settings Schemas
class QRSettingsBase(BaseModel):
    restaurant_name: str = Field(..., min_length=1, max_length=200)
    logo: Optional[str] = None
    primary_color: str = Field(default='#00A19D', pattern=r'^#[0-9A-Fa-f]{6}$')
    accent_color: str = Field(default='#FF6D00', pattern=r'^#[0-9A-Fa-f]{6}$')
    enable_online_ordering: bool = True
    enable_payment_at_table: bool = True
    enable_online_payment: bool = False
    service_charge_percentage: int = Field(default=1000, ge=0, le=10000)
    auto_confirm_orders: bool = False
    order_timeout_minutes: int = Field(default=30, ge=5, le=180)
    max_orders_per_session: int = Field(default=10, ge=1, le=100)
    enable_customer_info: bool = False
    enable_special_instructions: bool = True
    enable_order_tracking: bool = True
    welcome_message: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_address: Optional[str] = None
    business_hours: Optional[Dict] = None
    payment_gateways: List[str] = Field(default_factory=list)


class QRSettingsCreate(QRSettingsBase):
    pass


class QRSettingsUpdate(BaseModel):
    restaurant_name: Optional[str] = Field(None, min_length=1, max_length=200)
    logo: Optional[str] = None
    primary_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    accent_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    enable_online_ordering: Optional[bool] = None
    enable_payment_at_table: Optional[bool] = None
    enable_online_payment: Optional[bool] = None
    service_charge_percentage: Optional[int] = Field(None, ge=0, le=10000)
    auto_confirm_orders: Optional[bool] = None
    order_timeout_minutes: Optional[int] = Field(None, ge=5, le=180)
    max_orders_per_session: Optional[int] = Field(None, ge=1, le=100)
    enable_customer_info: Optional[bool] = None
    enable_special_instructions: Optional[bool] = None
    enable_order_tracking: Optional[bool] = None
    welcome_message: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_address: Optional[str] = None
    business_hours: Optional[Dict] = None
    payment_gateways: Optional[List[str]] = None


class QRSettingsResponse(QRSettingsBase):
    id: str
    updated_at: datetime
    
    @property
    def service_charge_percentage_display(self) -> float:
        return self.service_charge_percentage / 100
    
    class Config:
        from_attributes = True
