from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.cart.model import CartItemType, CartStatus
from app.modules.order.model import OrderType


class CartItemAddRequest(BaseModel):
    restaurant_id: str
    customer_id: str
    item_type: CartItemType
    product_id: Optional[str] = None
    combo_product_id: Optional[str] = None
    quantity: int = Field(1, ge=1)
    modifier_option_ids: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def _validate_item_type_ids(self):
        if self.item_type == CartItemType.PRODUCT:
            if not self.product_id:
                raise ValueError("product_id is required when item_type=product")
            if self.combo_product_id:
                raise ValueError("combo_product_id must be empty when item_type=product")
        if self.item_type == CartItemType.COMBO_PRODUCT:
            if not self.combo_product_id:
                raise ValueError("combo_product_id is required when item_type=combo_product")
            if self.product_id:
                raise ValueError("product_id must be empty when item_type=combo_product")
        return self


class CartItemUpdateRequest(BaseModel):
    quantity: int = Field(..., ge=1)


class CartProductSummary(BaseModel):
    """Current catalog details for a product line (may be null if product was removed)."""

    id: str
    name: str
    slug: str
    sku: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    price: int
    image: Optional[str] = None
    thumbnail: Optional[str] = None
    category_id: str
    category_name: Optional[str] = None
    available: bool

    model_config = ConfigDict(from_attributes=True)


class CartComboProductSummary(BaseModel):
    """Current catalog details for a combo line (may be null if combo was removed)."""

    id: str
    name: str
    slug: str
    description: Optional[str] = None
    price: int
    image: Optional[str] = None
    category_id: str
    category_name: Optional[str] = None
    available: bool
    featured: bool = False

    model_config = ConfigDict(from_attributes=True)


class CartItemResponse(BaseModel):
    id: str
    cart_id: str
    restaurant_id: str
    item_type: CartItemType
    product_id: Optional[str] = None
    combo_product_id: Optional[str] = None
    quantity: int
    unit_price: int
    modifiers_price: int
    total_price: int
    modifier_option_ids: List[str] = []
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    product: Optional[CartProductSummary] = None
    combo_product: Optional[CartComboProductSummary] = None

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: str
    restaurant_id: str
    customer_id: str
    status: CartStatus
    is_active: bool
    subtotal: int
    total_quantity: int
    items: List[CartItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartCheckoutRequest(BaseModel):
    """
    Order header fields for converting an active cart into an order.
    `restaurant_id` and `customer_id` come from the URL; line items are taken from the cart.
    """

    order_type: OrderType
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

