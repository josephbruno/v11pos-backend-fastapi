from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.modules.order.model import OrderType, OrderStatus, PaymentStatus, PaymentMethod


# Order Item Schemas
class OrderItemBase(BaseModel):
    """Base order item schema"""
    product_id: str
    product_name: str
    product_image: Optional[str] = None
    quantity: int = Field(..., ge=1, le=100)
    unit_price: int = Field(..., ge=0)
    modifiers: Optional[Dict[str, Any]] = None
    customization: Optional[str] = Field(None, max_length=1000)
    modifiers_price: int = Field(default=0, ge=0)
    discount_amount: int = Field(default=0, ge=0)
    tax_amount: int = Field(default=0, ge=0)
    department: Optional[str] = Field(None, max_length=50)
    printer_tag: Optional[str] = Field(None, max_length=50)
    is_complimentary: bool = False
    notes: Optional[str] = Field(None, max_length=1000)


class OrderItemCreate(OrderItemBase):
    """Schema for creating an order item"""

    is_combo_item: bool = False
    combo_id: Optional[str] = Field(None, max_length=36)


class OrderItemUpdate(BaseModel):
    """Schema for updating an order item"""
    quantity: Optional[int] = Field(None, ge=1, le=100)
    customization: Optional[str] = Field(None, max_length=1000)
    modifiers: Optional[Dict[str, Any]] = None
    modifiers_price: Optional[int] = Field(None, ge=0)
    discount_amount: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, max_length=20)
    is_complimentary: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=1000)


class OrderItemResponse(OrderItemBase):
    """Schema for order item response"""
    id: str
    order_id: str
    total_price: int
    status: Optional[str]
    preparation_started_at: Optional[datetime]
    preparation_completed_at: Optional[datetime]
    is_refunded: bool
    refund_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Order Schemas
class OrderBase(BaseModel):
    """Base order schema"""
    restaurant_id: str
    order_type: OrderType
    customer_id: Optional[str] = None
    table_id: Optional[str] = None
    guest_name: Optional[str] = Field(None, max_length=255)
    guest_phone: Optional[str] = Field(None, max_length=50)
    guest_email: Optional[str] = Field(None, max_length=255)
    delivery_address: Optional[str] = Field(None, max_length=500)
    delivery_latitude: Optional[float] = Field(None, ge=-90, le=90)
    delivery_longitude: Optional[float] = Field(None, ge=-180, le=180)
    delivery_instructions: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    guest_count: Optional[int] = Field(None, ge=1)
    special_instructions: Optional[str] = None
    kitchen_notes: Optional[str] = None
    staff_notes: Optional[str] = None
    discount_code: Optional[str] = Field(None, max_length=50)
    discount_type: Optional[str] = Field(None, max_length=20)
    source: Optional[str] = Field(None, max_length=50)
    source_details: Optional[Dict[str, Any]] = None
    is_priority: bool = False
    requires_cutlery: bool = True


class OrderCreate(OrderBase):
    """Schema for creating an order"""
    items: List[OrderItemCreate] = Field(..., min_length=1)


class OrderUpdate(BaseModel):
    """Schema for updating an order"""
    status: Optional[OrderStatus] = None
    customer_id: Optional[str] = None
    table_id: Optional[str] = None
    guest_name: Optional[str] = Field(None, max_length=255)
    guest_phone: Optional[str] = Field(None, max_length=50)
    guest_email: Optional[str] = Field(None, max_length=255)
    delivery_address: Optional[str] = Field(None, max_length=500)
    delivery_latitude: Optional[float] = Field(None, ge=-90, le=90)
    delivery_longitude: Optional[float] = Field(None, ge=-180, le=180)
    delivery_instructions: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    guest_count: Optional[int] = Field(None, ge=1)
    special_instructions: Optional[str] = None
    kitchen_notes: Optional[str] = None
    staff_notes: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None
    payment_status: Optional[PaymentStatus] = None
    discount_code: Optional[str] = Field(None, max_length=50)
    discount_amount: Optional[int] = Field(None, ge=0)
    delivery_fee: Optional[int] = Field(None, ge=0)
    service_charge: Optional[int] = Field(None, ge=0)
    tip_amount: Optional[int] = Field(None, ge=0)
    is_priority: Optional[bool] = None
    requires_cutlery: Optional[bool] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = None


class OrderResponse(OrderBase):
    """Schema for order response"""
    id: str
    order_number: str
    created_by: Optional[str]
    status: OrderStatus
    confirmed_at: Optional[datetime]
    preparing_at: Optional[datetime]
    ready_at: Optional[datetime]
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    subtotal: int
    tax_amount: int
    discount_amount: int
    delivery_fee: int
    service_charge: int
    tip_amount: int
    total_amount: int
    payment_status: PaymentStatus
    payment_method: Optional[PaymentMethod]
    payment_details: Optional[Dict[str, Any]]
    paid_amount: int
    is_takeaway_ready: bool
    rating: Optional[int]
    feedback: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    """Schema for paginated order list response"""
    total: int
    orders: List[OrderResponse]
    
    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    """Schema for updating order status only"""
    status: OrderStatus


class OrderPaymentUpdate(BaseModel):
    """Schema for updating order payment"""
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    paid_amount: int = Field(..., ge=0)
    payment_details: Optional[Dict[str, Any]] = None


class OrderAddItems(BaseModel):
    """Schema for adding items to existing order"""
    items: List[OrderItemCreate] = Field(..., min_length=1)


class OrderStatistics(BaseModel):
    """Schema for order statistics"""
    total_orders: int
    pending_orders: int
    confirmed_orders: int
    preparing_orders: int
    ready_orders: int
    completed_orders: int
    cancelled_orders: int
    total_revenue: int
    average_order_value: int
    
    model_config = ConfigDict(from_attributes=True)
