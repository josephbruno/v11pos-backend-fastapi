"""
Order related Pydantic schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from app.enums import OrderType, OrderStatus, PaymentStatus, OrderPriority


# Order Item Modifier Schema
class OrderItemModifierCreate(BaseModel):
    modifier_id: str
    modifier_name: str
    option_id: Optional[str] = None
    option_name: Optional[str] = None
    price: int = 0


class OrderItemModifierResponse(OrderItemModifierCreate):
    id: str
    order_item_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Order Item Schema
class OrderItemCreate(BaseModel):
    product_id: str
    combo_id: Optional[str] = None
    product_name: str
    quantity: int = Field(ge=1)
    unit_price: int = Field(ge=0)
    special_instructions: Optional[str] = None
    modifiers: List[OrderItemModifierCreate] = Field(default_factory=list)


class OrderItemResponse(BaseModel):
    id: str
    order_id: str
    product_id: str
    combo_id: Optional[str] = None
    product_name: str
    quantity: int
    unit_price: int
    total_price: int
    special_instructions: Optional[str] = None
    department: str
    kot_status: str
    kot_printed_at: Optional[datetime] = None
    created_at: datetime
    
    @property
    def unit_price_display(self) -> float:
        return self.unit_price / 100
    
    @property
    def total_price_display(self) -> float:
        return self.total_price / 100
    
    class Config:
        from_attributes = True


# Order Schema
class OrderBase(BaseModel):
    customer_id: Optional[str] = None
    customer_name: str = "Guest"
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    table_number: Optional[str] = None
    table_id: Optional[str] = None
    session_id: Optional[str] = None
    order_type: OrderType = OrderType.DINE_IN
    notes: Optional[str] = None
    delivery_address: Optional[str] = None


class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(..., min_length=1)
    discount_code: Optional[str] = None
    loyalty_points_redeemed: int = Field(default=0, ge=0)
    tip: int = Field(default=0, ge=0)


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    notes: Optional[str] = None
    priority: Optional[OrderPriority] = None


class OrderResponse(OrderBase):
    id: str
    order_number: str
    status: OrderStatus
    payment_status: PaymentStatus
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    subtotal: int
    tax_total: int
    service_charge: int
    discount: int
    discount_code: Optional[str] = None
    loyalty_points_redeemed: int
    loyalty_points_earned: int
    tip: int
    total: int
    estimated_time: int
    priority: OrderPriority
    created_at: datetime
    accepted_at: Optional[datetime] = None
    preparing_at: Optional[datetime] = None
    ready_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    @property
    def subtotal_display(self) -> float:
        return self.subtotal / 100
    
    @property
    def total_display(self) -> float:
        return self.total / 100
    
    class Config:
        from_attributes = True


class OrderWithItemsResponse(OrderResponse):
    items: List[OrderItemResponse] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


# Order Status Update Schema
class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    notes: Optional[str] = None


# Payment Schema
class PaymentCreate(BaseModel):
    payment_method: str = Field(..., min_length=1)
    transaction_id: Optional[str] = None
    amount: int = Field(..., gt=0)
